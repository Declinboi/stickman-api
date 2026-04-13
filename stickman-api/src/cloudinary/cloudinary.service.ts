import {
  Injectable,
  InternalServerErrorException,
  Logger,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { v2 as cloudinary, UploadApiResponse } from 'cloudinary';
import { Readable } from 'stream';
import { retryWithBackoff } from '../common/utils/retry.util';
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
    return retryWithBackoff(
      () => this._doUpload(fileBuffer, originalName),
      {
        attempts: 3,
        delay: 2000,
        backoff: 'exponential',
        onRetry: (error, attempt) => {
          this.logger.warn(
            `Cloudinary upload retry #${attempt} for "${originalName}": ${(error as Error)?.message}`,
          );
        },
      },
      this.logger,
      'CloudinaryService.uploadVideo',
    );
  }
  /** Raw upload — called by retryWithBackoff */
  private _doUpload(
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
          if (!result) {
            return reject(
              new InternalServerErrorException('Cloudinary returned no result'),
            );
          }
          resolve(result);
        },
      );
      const readable = new Readable();
      readable.push(fileBuffer);
      readable.push(null);
      readable.pipe(uploadStream);
    });
  }
  async deleteVideo(publicId: string): Promise<void> {
    await retryWithBackoff(
      () =>
        cloudinary.uploader
          .destroy(publicId, { resource_type: 'video' })
          .then((result) => {
            // Cloudinary resolves even on "not found"; treat explicit errors only
            if (result?.result === 'error') {
              throw new Error(
                `Cloudinary destroy error for publicId "${publicId}": ${JSON.stringify(result)}`,
              );
            }
          }),
      {
        attempts: 3,
        delay: 1000,
        backoff: 'exponential',
        onRetry: (error, attempt) => {
          this.logger.warn(
            `Cloudinary delete retry #${attempt} for "${publicId}": ${(error as Error)?.message}`,
          );
        },
      },
      this.logger,
      'CloudinaryService.deleteVideo',
    );
    this.logger.log(`Deleted video: ${publicId}`);
  }
  getVideoUrl(publicId: string): string {
    return cloudinary.url(publicId, { resource_type: 'video' });
  }
  async getSignedDownloadUrl(
    publicId: string,
    expiresIn: number = 3600,
  ): Promise<string> {
    return cloudinary.url(publicId, {
      resource_type: 'video',
      type: 'upload',
      sign_url: true,
      expires_at: Math.floor(Date.now() / 1000) + expiresIn,
      flags: 'attachment',
    });
  }
}
