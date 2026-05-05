import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SharedImportModule } from '../../shared-import/shared-import-module';
import { NotificationDialog } from './notification-dialog/notification-dialog';

@NgModule({
  declarations: [NotificationDialog],
  imports: [CommonModule, SharedImportModule],
  exports: [NotificationDialog],
})
export class SharedModule {}
