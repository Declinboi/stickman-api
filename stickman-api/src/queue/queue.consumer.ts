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

@Processor(VIDEO_PROCESSING_QUEUE)
export class QueueConsumer extends WorkerHost {
  private readonly logger = new Logger(QueueConsumer.name);

  constructor(
    private readonly jobsService: JobsService,
    private readonly httpService: HttpService,
    private readonly config: ConfigService,
  ) {
    super();
  }

  async process(job: Job<VideoJobPayload>): Promise<void> {
    const { jobId, inputVideoUrl, originalFilename } = job.data;

    this.logger.log(`Processing job ${jobId} — ${originalFilename}`);

    try {
      // 1. Mark job as processing in PostgreSQL
      await this.jobsService.updateStatus(jobId, JobStatus.PROCESSING, {
        progress: 0,
      });

      // 2. Call the Python pose estimation service
      const pythonServiceUrl = this.config.get<string>(
        'PYTHON_SERVICE_URL',
        'http://localhost:8000',
      );

      this.logger.log(`Calling Python service at ${pythonServiceUrl}`);

      const response = await firstValueFrom(
        this.httpService.post(
          `${pythonServiceUrl}/process`,
          {
            job_id: jobId,
            input_video_url: inputVideoUrl,
          },
          {
            timeout: 10 * 60 * 1000, // 10 minute timeout for long videos
          },
        ),
      );

      const { output_video_url } = response.data;

      // 3. Mark job as completed with output URL
      await this.jobsService.updateStatus(jobId, JobStatus.COMPLETED, {
        progress: 100,
        outputVideoUrl: output_video_url,
      });

      this.logger.log(`Job ${jobId} completed — output: ${output_video_url}`);
    } catch (error) {
      this.logger.error(`Job ${jobId} failed`, error);

      // Mark job as failed with error message
      await this.jobsService.updateStatus(jobId, JobStatus.FAILED, {
        errorMessage:
          error?.response?.data?.detail ?? error.message ?? 'Processing failed',
      });

      // Re-throw so BullMQ knows the job failed and can retry
      throw error;
    }
  }

  @OnWorkerEvent('active')
  onActive(job: Job) {
    this.logger.log(`Job ${job.id} started processing`);
  }

  @OnWorkerEvent('completed')
  onCompleted(job: Job) {
    this.logger.log(`Job ${job.id} completed successfully`);
  }

  @OnWorkerEvent('failed')
  onFailed(job: Job, error: Error) {
    this.logger.error(`Job ${job.id} failed: ${error.message}`);
  }
}
