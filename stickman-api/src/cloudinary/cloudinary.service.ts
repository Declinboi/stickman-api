import {
  Injectable,
  InternalServerErrorException,
  Logger,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { v2 as cloudinary, UploadApiResponse } from 'cloudinary';
import { Readable } from 'stream';

@Injectable()
export class CloudinaryService {
  private readonly logger = new Logger(CloudinaryService.name);

  constructor(private config: ConfigService) {
    cloudinary.config({
      cloud_name: this.config.get<string>('CLOUDINARY_CLOUD_NAME'),
      api_key: this.config.get<string>('CLOUDINARY_API_KEY'),
      api_secret: this.config.get<string>('CLOUDINARY_API_SECRET'),
    });
  }

  async uploadVideo(
    fileBuffer: Buffer,
    originalName: string,
  ): Promise<UploadApiResponse> {
    return new Promise((resolve, reject) => {
      const uploadStream = cloudinary.uploader.upload_stream(
        {
          resource_type: 'video',
          folder: 'stickman/inputs',
          public_id: `${Date.now()}-${originalName.replace(/\.[^/.]+$/, '')}`,
          overwrite: false,
        },
        (error, result) => {
          if (error) {
            this.logger.error('Cloudinary upload failed', error);
            return reject(error);
          }

          // Fix: guard against undefined result before resolving
          if (!result) {
            return reject(
              new InternalServerErrorException('Cloudinary returned no result'),
            );
          }
          resolve(result);
        },
      );

      // Convert buffer to stream and pipe into Cloudinary
      const readable = new Readable();
      readable.push(fileBuffer);
      readable.push(null);
      readable.pipe(uploadStream);
    });
  }

  async deleteVideo(publicId: string): Promise<void> {
    await cloudinary.uploader.destroy(publicId, { resource_type: 'video' });
    this.logger.log(`Deleted video: ${publicId}`);
  }

  getVideoUrl(publicId: string): string {
    return cloudinary.url(publicId, { resource_type: 'video' });
  }
}
