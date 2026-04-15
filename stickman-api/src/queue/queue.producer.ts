// queue.producer.ts
import { Injectable, Logger } from '@nestjs/common';
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';
import { VIDEO_PROCESSING_QUEUE, JobEvents } from './queue.constants';

export interface VideoJobPayload {
  jobId: string;
  userId: string;
  description: string;
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
      attempts: 3,
      backoff: {
        type: 'exponential',
        delay: 5000,
      },
      removeOnComplete: 100,
      removeOnFail: 50,
    });

    this.logger.log(`Fight generation job queued for jobId: ${payload.jobId}`);
  }
}
