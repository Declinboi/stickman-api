import { Module, Global } from '@nestjs/common';
import { VideoGateway } from './video.gateway';

@Global() // makes VideoGateway injectable anywhere without re-importing
@Module({
  providers: [VideoGateway],
  exports: [VideoGateway],
})
export class GatewayModule {}
