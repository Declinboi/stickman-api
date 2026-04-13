import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { DatabaseModule } from './database/database.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true, // makes .env available everywhere without re-importing
    }),
    DatabaseModule,
  ],
})
export class AppModule {}