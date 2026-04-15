import {
  Injectable,
  NotFoundException,
  ForbiddenException,
  BadRequestException,
} from '@nestjs/common';
import { JobsService } from '../jobs/jobs.service';
import { CloudinaryService } from '../cloudinary/cloudinary.service';
import { JobStatus } from '../entities/job.entity';

@Injectable()
export class DownloadService {
  constructor(
    private readonly jobsService: JobsService,
    private readonly cloudinaryService: CloudinaryService,
  ) {}

  async getDownloadUrl(
    jobId: string,
    userId: string,
  ): Promise<{ downloadUrl: string; expiresIn: number }> {
    // 1. Fetch the job and verify it belongs to this user
    const job = await this.jobsService.findOne(jobId, userId);

    // 2. Make sure the job actually belongs to this user
    if (job.userId !== userId) {
      throw new ForbiddenException('You do not have access to this job');
    }

    // 3. Make sure the job is completed
    if (job.status !== JobStatus.COMPLETED) {
      throw new BadRequestException(
        `Job is not completed yet. Current status: ${job.status}`,
      );
    }

    // 4. Make sure output video exists
    if (!job.outputVideoUrl) {
      throw new NotFoundException('Output video not found for this job');
    }

    // 5. Extract the Cloudinary public_id from the output URL
    const publicId = this.extractPublicId(job.outputVideoUrl);

    // 6. Generate a signed Cloudinary URL (valid for 1 hour)
    const expiresIn = 3600; // seconds
    const downloadUrl = await this.cloudinaryService.getSignedDownloadUrl(
      publicId,
      expiresIn,
    );

    // 7. Build a clean output filename
    // const filename = `stickman-${job.originalFilename}`;

    return { downloadUrl, expiresIn };
  }

  async getJobResult(
    jobId: string,
    userId: string,
  ): Promise<{
    jobId: string;
    status: string;
    progress: number;
    // originalFilename: string;
    outputVideoUrl: string | null;
    downloadUrl: string | null;
    duration: number | null;
    createdAt: Date;
    updatedAt: Date;
  }> {
    const job = await this.jobsService.findOne(jobId, userId);

    let downloadUrl: string | null = null;

    // Only generate download URL if job is completed
    if (job.status === JobStatus.COMPLETED && job.outputVideoUrl) {
      const publicId = this.extractPublicId(job.outputVideoUrl);
      downloadUrl = await this.cloudinaryService.getSignedDownloadUrl(
        publicId,
        3600,
      );
    }

    return {
      jobId: job.id,
      status: job.status,
      progress: job.progress,
      // originalFilename: job.originalFilename,
      outputVideoUrl: job.outputVideoUrl ?? null,
      downloadUrl,
      duration: job.duration ?? null,
      createdAt: job.createdAt,
      updatedAt: job.updatedAt,
    };
  }

  private extractPublicId(cloudinaryUrl: string): string {
    // Cloudinary URL format:
    // https://res.cloudinary.com/<cloud>/video/upload/v123456/stickman/outputs/output-jobid.mp4
    // We need: stickman/outputs/output-jobid
    const matches = cloudinaryUrl.match(
      /\/upload\/(?:v\d+\/)?(.+?)(?:\.[a-zA-Z0-9]+)?$/,
    );

    if (!matches || !matches[1]) {
      throw new BadRequestException(
        'Could not extract public ID from video URL',
      );
    }

    return matches[1];
  }
}
