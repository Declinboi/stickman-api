import { Injectable, Logger } from '@nestjs/common';
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';
import { VIDEO_PROCESSING_QUEUE, JobEvents } from './queue.constants';

export interface VideoJobPayload {
  jobId: string;
  userId: string;
  inputVideoUrl: string;
  originalFilename: string;
}

@Injectable()
export class QueueProducer {
  private readonly logger = new Logger(QueueProducer.name);

  constructor(
    @InjectQueue(VIDEO_PROCESSING_QUEUE)
    private readonly videoQueue: Queue,
  ) {}

  async addVideoProcessingJob(payload: VideoJobPayload): Promise<void> {
    await this.videoQueue.add(JobEvents.PROCESS_VIDEO, payload, {
      attempts: 3, // retry up to 3 times on failure
      backoff: {
        type: 'exponential',
        delay: 5000, // wait 5s, 10s, 20s between retries
      },
      removeOnComplete: 100, // keep last 100 completed jobs in Redis
      removeOnFail: 50, // keep last 50 failed jobs in Redis
    });

    this.logger.log(`Video processing job queued for jobId: ${payload.jobId}`);
  }
}
