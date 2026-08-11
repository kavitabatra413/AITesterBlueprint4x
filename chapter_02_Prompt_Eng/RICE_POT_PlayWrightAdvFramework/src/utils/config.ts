import * as dotenv from 'dotenv';
import path from 'path';

dotenv.config({ path: path.resolve(__dirname, '../../.env') });

export const config = {
  baseUrl: process.env.BASE_URL ?? 'https://login.salesforce.com/?locale=in',
  validUsername: process.env.VALID_USERNAME ?? '',
  validPassword: process.env.VALID_PASSWORD ?? '',
  invalidPassword: process.env.INVALID_PASSWORD ?? 'wrong_password',
  explicitTimeout: Number(process.env.EXPLICIT_TIMEOUT ?? 15000),
  headless: process.env.HEADLESS !== 'false',
};
