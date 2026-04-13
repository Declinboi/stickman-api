import {
  Controller,
  Post,
  UploadedFile,
  UseInterceptors,
  Request,
  BadRequestException,
  UseGuards,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { memoryStorage } from 'multer';
import { UploadService } from './upload.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';

@Controller('upload')
@UseGuards(JwtAuthGuard) // protects all routes in this controller
export class UploadController {
  constructor(private readonly uploadService: UploadService) {}

  @Post('video')
  @UseInterceptors(
    FileInterceptor('video', {
      storage: memoryStorage(),
      limits: { fileSize: 200 * 1024 * 1024 },
      fileFilter: (req, file, callback) => {
        const allowed = [
          'video/mp4',
          'video/mpeg',
          'video/quicktime',
          'video/avi',
        ];
        if (!allowed.includes(file.mimetype)) {
          return callback(
            new BadRequestException('Only video files are allowed'),
            false,
          );
        }
        callback(null, true);
      },
    }),
  )
  async uploadVideo(@UploadedFile() file: Express.Multer.File, @Request() req) {
    if (!file) throw new BadRequestException('No video file provided');

    // req.user.id now comes from the real JWT token
    const job = await this.uploadService.handleVideoUpload(file, req.user.id);

    return {
      message: 'Video uploaded successfully. Processing will begin shortly.',
      jobId: job.id,
      status: job.status,
      originalFilename: job.originalFilename,
      createdAt: job.createdAt,
    };
  }
}
