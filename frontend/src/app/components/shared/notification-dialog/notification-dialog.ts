import { Component, Inject, ChangeDetectionStrategy } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { NotificationDialogData } from './notification-dialog.model';

@Component({
  selector: 'app-notification-dialog',
  standalone: false,
  templateUrl: './notification-dialog.html',
  styleUrl: './notification-dialog.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NotificationDialog {
  constructor(
    public dialogRef: MatDialogRef<NotificationDialog>,
    @Inject(MAT_DIALOG_DATA) public data: NotificationDialogData,
  ) {}

  get icon(): string {
    const icons: Record<NotificationDialogData['type'], string> = {
      success: 'check_circle',
      error: 'error',
      warning: 'warning',
    };
    return icons[this.data.type];
  }

  close(): void {
    this.dialogRef.close();
  }
}
