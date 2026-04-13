import { Injectable } from '@nestjs/common';
import { CloudinaryService } from '../cloudinary/cloudinary.service';
import { JobsService } from '../jobs/jobs.service';
import { QueueProducer } from '../queue/queue.producer';
import { Job } from '../entities/job.entity';

@Injectable()
export class UploadService {
  constructor(
    private readonly cloudinaryService: CloudinaryService,
    private readonly jobsService: JobsService,
    private readonly queueProducer: QueueProducer,
  ) {}

  async handleVideoUpload(
    file: Express.Multer.File,
    userId: string,
  ): Promise<Job> {
    // 1. Upload video to Cloudinary
    const uploaded = await this.cloudinaryService.uploadVideo(
      file.buffer,
      file.originalname,
    );

    // 2. Create job record in PostgreSQL
    const job = await this.jobsService.createJob({
      originalFilename: file.originalname,
      inputVideoUrl: uploaded.secure_url,
      userId,
      duration: Math.round(uploaded.duration ?? 0),
    });

    // 3. Push job into BullMQ queue for processing
    await this.queueProducer.addVideoProcessingJob({
      jobId: job.id,
      userId,
      inputVideoUrl: uploaded.secure_url,
      originalFilename: file.originalname,
    });

    return job;
  }
}
