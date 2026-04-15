import {
  Controller,
  Post,
  Body,
  Request,
  BadRequestException,
  UseGuards,
} from '@nestjs/common';
import { UploadService } from './upload.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';

@Controller('upload')
@UseGuards(JwtAuthGuard)
export class UploadController {
  constructor(private readonly uploadService: UploadService) {}

  @Post('generate')
  async generate(@Body('description') description: string, @Request() req) {
    if (!description?.trim()) {
      throw new BadRequestException('Fight description is required');
    }

    const job = await this.uploadService.handleGenerateRequest(
      description.trim(),
      req.user.id,
    );

    return {
      message: 'Fight generation queued. Animation will be ready shortly.',
      jobId: job.id,
      status: job.status,
      createdAt: job.createdAt,
    };
  }
}
