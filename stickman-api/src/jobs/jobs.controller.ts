import { Controller, Get, Param, Request } from '@nestjs/common';
import { JobsService } from './jobs.service';

@Controller('jobs')
export class JobsController {
  constructor(private readonly jobsService: JobsService) {}

  // GET /jobs — get all jobs for the logged-in user
  @Get()
  findAll(@Request() req) {
    const userId = req.user?.id ?? 'temp-user-id'; // replace with real auth later
    return this.jobsService.findAllByUser(userId);
  }

  // GET /jobs/:id — get a single job status
  @Get(':id')
  findOne(@Param('id') id: string, @Request() req) {
    const userId = req.user?.id ?? 'temp-user-id';
    return this.jobsService.findOne(id, userId);
  }
}
