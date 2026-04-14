import {
  Controller,
  Get,
  Param,
  Request,
  UseGuards,
  UnauthorizedException,
} from '@nestjs/common';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { JobsService } from './jobs.service';

@Controller('jobs')
@UseGuards(JwtAuthGuard) // protect all routes in this controller
export class JobsController {
  constructor(private readonly jobsService: JobsService) {}

  @Get()
  findAll(@Request() req) {
    return this.jobsService.findAllByUser(req.user.id);
  }

  @Get(':id')
  findOne(@Param('id') id: string, @Request() req) {
    return this.jobsService.findOne(id, req.user.id);
  }
}
