import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Job, JobStatus } from '../entities/job.entity';

@Injectable()
export class JobsService {
  constructor(
    @InjectRepository(Job)
    private jobRepository: Repository<Job>,
  ) {}

  async createJob(data: {
    originalFilename: string;
    inputVideoUrl: string;
    userId: string;
    duration?: number;
  }): Promise<Job> {
    const job = this.jobRepository.create({
      originalFilename: data.originalFilename,
      inputVideoUrl: data.inputVideoUrl,
      userId: data.userId,
      duration: data.duration,
      status: JobStatus.PENDING,
      progress: 0,
    });
    return this.jobRepository.save(job);
  }

  async findAllByUser(userId: string): Promise<Job[]> {
    return this.jobRepository.find({
      where: { userId },
      order: { createdAt: 'DESC' },
    });
  }

  async findOne(id: string, userId: string): Promise<Job> {
    const job = await this.jobRepository.findOne({
      where: { id, userId },
    });
    if (!job) throw new NotFoundException(`Job ${id} not found`);
    return job;
  }

  async updateStatus(
    id: string,
    status: JobStatus,
    extra?: {
      progress?: number;
      outputVideoUrl?: string;
      errorMessage?: string;
    },
  ): Promise<Job> {
    await this.jobRepository.update(id, { status, ...extra });
    // Fix: handle the null case after fetching
    const updated = await this.jobRepository.findOne({ where: { id } });
    if (!updated) throw new NotFoundException(`Job ${id} not found`);
    return updated;
  }

  async deleteJob(id: string, userId: string): Promise<void> {
    const job = await this.jobRepository.findOne({ where: { id, userId } });
    if (!job) throw new NotFoundException(`Job ${id} not found`);
    await this.jobRepository.delete(id);
  }
}
