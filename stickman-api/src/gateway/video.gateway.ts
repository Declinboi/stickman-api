import {
  WebSocketGateway,
  WebSocketServer,
  SubscribeMessage,
  OnGatewayConnection,
  OnGatewayDisconnect,
  OnGatewayInit,
  MessageBody,
  ConnectedSocket,
} from '@nestjs/websockets';
import { Logger } from '@nestjs/common';
import { Server, Socket } from 'socket.io';

@WebSocketGateway({
  cors: {
    origin: '*',
  },
  namespace: '/video',
})
export class VideoGateway
  implements OnGatewayInit, OnGatewayConnection, OnGatewayDisconnect
{
  @WebSocketServer()
  server: Server;

  private readonly logger = new Logger(VideoGateway.name);
  private jobSubscriptions = new Map<string, Set<string>>();

  afterInit() {
    this.logger.log('WebSocket Gateway initialized');
  }

  handleConnection(client: Socket) {
    this.logger.log(`Client connected: ${client.id}`);
  }

  handleDisconnect(client: Socket) {
    this.logger.log(`Client disconnected: ${client.id}`);

    this.jobSubscriptions.forEach((sockets, jobId) => {
      sockets.delete(client.id);
      if (sockets.size === 0) {
        this.jobSubscriptions.delete(jobId);
      }
    });
  }

  @SubscribeMessage('subscribe_job')
  handleSubscribeJob(
    @MessageBody() data: { jobId: string },
    @ConnectedSocket() client: Socket,
  ) {
    const { jobId } = data;

    // Fix: store the set in a variable so TypeScript can narrow the type
    let sockets = this.jobSubscriptions.get(jobId);
    if (!sockets) {
      sockets = new Set<string>();
      this.jobSubscriptions.set(jobId, sockets);
    }
    sockets.add(client.id); // ← sockets is guaranteed Set<string> here, never undefined

    client.join(`job:${jobId}`);
    this.logger.log(`Client ${client.id} subscribed to job ${jobId}`);

    return { event: 'subscribed', jobId };
  }

  @SubscribeMessage('unsubscribe_job')
  handleUnsubscribeJob(
    @MessageBody() data: { jobId: string },
    @ConnectedSocket() client: Socket,
  ) {
    const { jobId } = data;

    this.jobSubscriptions.get(jobId)?.delete(client.id); // ← optional chaining fine here since we don't need the value
    client.leave(`job:${jobId}`);
    this.logger.log(`Client ${client.id} unsubscribed from job ${jobId}`);

    return { event: 'unsubscribed', jobId };
  }

  emitJobProgress(jobId: string, progress: number) {
    this.server.to(`job:${jobId}`).emit('job_progress', {
      jobId,
      progress,
      status: 'processing',
    });
    this.logger.log(`Emitted progress ${progress}% for job ${jobId}`);
  }

  emitJobCompleted(jobId: string, outputVideoUrl: string) {
    this.server.to(`job:${jobId}`).emit('job_completed', {
      jobId,
      progress: 100,
      status: 'completed',
      outputVideoUrl,
    });
    this.logger.log(`Emitted completed for job ${jobId}`);
  }

  emitJobFailed(jobId: string, errorMessage: string) {
    this.server.to(`job:${jobId}`).emit('job_failed', {
      jobId,
      status: 'failed',
      errorMessage,
    });
    this.logger.log(`Emitted failed for job ${jobId}`);
  }
}
