import {
  IsEmail,
  IsString,
  MinLength,
  MaxLength,
  IsOptional,
} from 'class-validator';

export class RegisterDto {
  @IsEmail({}, { message: 'Please provide a valid email' })
  email: string;

  @IsString()
  @MinLength(6, { message: 'Password must be at least 6 characters' })
  @MaxLength(32, { message: 'Password must not exceed 32 characters' })
  password: string;

  @IsOptional()
  @IsString()
  @MinLength(2)
  @MaxLength(30)
  username?: string;
}
