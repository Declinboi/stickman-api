import { Processor, WorkerHost, OnWorkerEvent } from '@nestjs/bullmq';
import { Logger } from '@nestjs/common';
import { Job } from 'bullmq';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { firstValueFrom } from 'rxjs';
import { VIDEO_PROCESSING_QUEUE, JobEvents } from './queue.constants';
import { JobsService } from '../jobs/jobs.service';
import { JobStatus } from '../entities/job.entity';
import { VideoJobPayload } from './queue.producer';
import { VideoGateway } from '../gateway/video.gateway';
import { retryWithBackoff } from '../common/utils/retry.util';
@Processor(VIDEO_PROCESSING_QUEUE)
export class QueueConsumer extends WorkerHost {
  private readonly logger = new Logger(QueueConsumer.name);
  constructor(
    private readonly jobsService: JobsService,
    private readonly httpService: HttpService,
    private readonly config: ConfigService,
    private readonly videoGateway: VideoGateway,
  ) {
    super();
  }
  async process(job: Job<VideoJobPayload>): Promise<void> {
    const { jobId, inputVideoUrl, originalFilename } = job.data;
    this.logger.log(`Processing job ${jobId} — ${originalFilename}`);
    try {
      // 1. Mark as processing in PostgreSQL + emit via WebSocket
      await this.jobsService.updateStatus(jobId, JobStatus.PROCESSING, {
        progress: 0,
      });
      this.videoGateway.emitJobProgress(jobId, 0);
      // 2. Emit progress — downloading phase
      this.videoGateway.emitJobProgress(jobId, 5);
      const pythonServiceUrl = this.config.get<string>('PYTHON_SERVICE_URL');
      // 3. Emit progress — processing started
      this.videoGateway.emitJobProgress(jobId, 10);
      this.logger.log(`Calling Python service for job ${jobId}`);
      // 4. Call Python service with retry logic
      //    - 3 attempts total (1 original + 2 retries)
      //    - Exponential backoff: 3s → 6s between retries
      //    - Per-attempt timeout: 10 minutes (the job itself may be long)
      //    - NOTE: BullMQ also retries the whole job (see QueueProducer),
      //      so these inner retries handle transient network/HTTP errors only.
      const response = await retryWithBackoff(
        () =>
          firstValueFrom(
            this.httpService.post(
              `${pythonServiceUrl}/process`,
              {
                job_id: jobId,
                input_video_url: inputVideoUrl,
              },
              {
                timeout: 10 * 60 * 1000, // 10 min per attempt
              },
            ),
          ),
        {
          attempts: 3,
          delay: 3000,
          backoff: 'exponential',
          onRetry: (error: unknown, attempt: number) => {
            const msg =
              (error as any)?.response?.data?.detail ??
              (error as Error)?.message ??
              'unknown error';
            this.logger.warn(
              `Python service retry #${attempt} for job ${jobId}: ${msg}`,
            );
            // Keep the frontend informed that we are still working
            this.videoGateway.emitJobProgress(jobId, 10 + attempt * 2);
          },
        },
        this.logger,
        `QueueConsumer.process[${jobId}]`,
      );
      // 5. Emit near-complete progress before final save
      this.videoGateway.emitJobProgress(jobId, 95);
      const { output_video_url } = response.data;
      // 6. Mark as completed in PostgreSQL
      await this.jobsService.updateStatus(jobId, JobStatus.COMPLETED, {
        progress: 100,
        outputVideoUrl: output_video_url,
      });
      // 7. Emit completed event with output URL
      this.videoGateway.emitJobCompleted(jobId, output_video_url);
      this.logger.log(`Job ${jobId} completed — ${output_video_url}`);
    } catch (error) {
      this.logger.error(`Job ${jobId} failed`, error);
      const errorMessage =
        (error as any)?.response?.data?.detail ??
        (error as Error)?.message ??
        'Processing failed';
      // Update DB
      await this.jobsService.updateStatus(jobId, JobStatus.FAILED, {
        errorMessage,
      });
      // Emit failure to frontend
      this.videoGateway.emitJobFailed(jobId, errorMessage);
      // Re-throw so BullMQ can apply its own job-level retry / backoff
      throw error;
    }
  }
  @OnWorkerEvent('active')
  onActive(job: Job) {
    this.logger.log(`Job ${job.id} is now active`);
  }
  @OnWorkerEvent('completed')
  onCompleted(job: Job) {
    this.logger.log(`Job ${job.id} completed`);
  }
  @OnWorkerEvent('failed')
  onFailed(job: Job, error: Error) {
    this.logger.error(`Job ${job.id} failed: ${error.message}`);
  }
}
