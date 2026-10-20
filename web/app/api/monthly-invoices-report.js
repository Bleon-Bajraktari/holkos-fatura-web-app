import nodemailer from 'nodemailer'
import { createMonthlyHandler } from '../lib/monthly-report.js'

export const config = { maxDuration: 60 }
export default createMonthlyHandler({ createTransport: options => nodemailer.createTransport(options) })
