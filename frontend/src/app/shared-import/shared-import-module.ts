import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDialogModule } from '@angular/material/dialog';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDividerModule } from '@angular/material/divider';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatChipsModule } from '@angular/material/chips';
import { MatListModule } from '@angular/material/list';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatBadgeModule } from '@angular/material/badge';
import { MatMenuModule } from '@angular/material/menu';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatTabsModule } from '@angular/material/tabs';
import { MatProgressBarModule } from '@angular/material/progress-bar';

const materialModules = [
  MatCardModule,
  MatFormFieldModule,
  MatInputModule,
  MatButtonModule,
  MatIconModule,
  MatDialogModule,
  MatSlideToggleModule,
  MatProgressSpinnerModule,
  MatDividerModule,
  MatToolbarModule,
  MatExpansionModule,
  MatChipsModule,
  MatListModule,
  MatTooltipModule,
  MatSnackBarModule,
  MatBadgeModule,
  MatMenuModule,
  MatAutocompleteModule,
  MatTabsModule,
  MatProgressBarModule,
];

@NgModule({
  declarations: [],
  exports: [CommonModule, ReactiveFormsModule, FormsModule, ...materialModules],
  imports: [CommonModule, ReactiveFormsModule, FormsModule, ...materialModules],
})
export class SharedImportModule {}
