import { Module } from '@nestjs/common';
import { BullModule } from '@nestjs/bullmq';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { HttpModule } from '@nestjs/axios';
import { QueueProducer } from './queue.producer';
import { QueueConsumer } from './queue.consumer';
import { VIDEO_PROCESSING_QUEUE } from './queue.constants';
import { JobsModule } from '../jobs/jobs.module';
import { GatewayModule } from 'src/gateway/gateway.module';

@Module({
  imports: [
    // Register BullMQ with Redis connection from .env
    BullModule.forRootAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        connection: {
          host: config.get<string>('REDIS_HOST', 'localhost'),
          port: config.get<number>('REDIS_PORT', 6379),
        },
      }),
    }),

    // Register the specific queue
    BullModule.registerQueue({
      name: VIDEO_PROCESSING_QUEUE,
    }),

    HttpModule, // for calling the Python service
    JobsModule,
    GatewayModule,
  ],
  providers: [QueueProducer, QueueConsumer],
  exports: [QueueProducer],
})
export class QueueModule {}
