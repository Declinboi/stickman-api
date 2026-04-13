import { Module } from '@nestjs/common';
import { UploadController } from './upload.controller';
import { UploadService } from './upload.service';
import { JobsModule } from '../jobs/jobs.module';
import { QueueModule } from '../queue/queue.module';

@Module({
  imports: [JobsModule, QueueModule],
  controllers: [UploadController],
  providers: [UploadService],
})
export class UploadModule {}
