import {
  Controller,
  Get,
  Param,
  Request,
  UseGuards,
  Res,
} from '@nestjs/common';
import type { Response } from 'express';
import { DownloadService } from './download.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';

@Controller('download')
@UseGuards(JwtAuthGuard)
export class DownloadController {
  constructor(private readonly downloadService: DownloadService) {}

  /**
   * GET /download/:jobId
   * Returns a signed Cloudinary download URL valid for 1 hour.
   * Frontend uses this URL to trigger the actual file download.
   */
  @Get(':jobId')
  async getDownloadUrl(@Param('jobId') jobId: string, @Request() req) {
    const result = await this.downloadService.getDownloadUrl(
      jobId,
      req.user.id,
    );

    return {
      message: 'Download link generated successfully',
      ...result,
    };
  }

  /**
   * GET /download/:jobId/result
   * Returns full job result including status, outputVideoUrl,
   * and a signed download URL if completed.
   * Useful for the frontend to show a results page.
   */
  @Get(':jobId/result')
  async getJobResult(@Param('jobId') jobId: string, @Request() req) {
    return this.downloadService.getJobResult(jobId, req.user.id);
  }

  /**
   * GET /download/:jobId/redirect
   * Redirects the browser directly to the signed Cloudinary URL.
   * Useful if you want a direct download link that works in <a href>.
   */
  @Get(':jobId/redirect')
  async redirectToDownload(
    @Param('jobId') jobId: string,
    @Request() req,
    @Res() res: Response,
  ) {
    const { downloadUrl } = await this.downloadService.getDownloadUrl(
      jobId,
      req.user.id,
    );

    return res.redirect(downloadUrl);
  }
}
