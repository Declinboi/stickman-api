import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  ManyToOne,
  JoinColumn,
} from 'typeorm';
import { User } from './user.entity';

export enum JobStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

@Entity('jobs')
export class Job {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  originalFilename: string;

  @Column()
  inputVideoUrl: string;

  @Column({ nullable: true })
  outputVideoUrl: string;

  @Column({
    type: 'enum',
    enum: JobStatus,
    default: JobStatus.PENDING,
  })
  status: JobStatus;

  @Column({ nullable: true })
  errorMessage: string;

  @Column({ type: 'int', default: 0 })
  progress: number; // 0–100

  @Column({ nullable: true })
  duration: number; // video duration in seconds

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;

  @ManyToOne(() => User, (user) => user.jobs, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'userId' })
  user: User;

  @Column()
  userId: string;
}
