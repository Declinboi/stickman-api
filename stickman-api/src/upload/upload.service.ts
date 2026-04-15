import { Injectable } from '@nestjs/common';
import { JobsService } from '../jobs/jobs.service';
import { QueueProducer } from '../queue/queue.producer';
import { Job } from '../entities/job.entity';

@Injectable()
export class UploadService {
  constructor(
    private readonly jobsService: JobsService,
    private readonly queueProducer: QueueProducer,
  ) {}

  async handleGenerateRequest(
    description: string,
    userId: string,
  ): Promise<Job> {
    // 1. Create job record in PostgreSQL
    const job = await this.jobsService.createJob({ description, userId });

    // 2. Push job into BullMQ queue for processing
    await this.queueProducer.addVideoProcessingJob({
      jobId: job.id,
      userId,
      description,
    });

    return job;
  }
}