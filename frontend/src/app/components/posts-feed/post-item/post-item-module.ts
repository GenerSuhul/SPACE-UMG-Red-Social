import { NgModule } from '@angular/core';
import { SharedImportModule } from '../../../shared-import/shared-import-module';
import { PostItem } from './post-item';

@NgModule({
  declarations: [PostItem],
  imports: [SharedImportModule],
  exports: [PostItem],
})
export class PostItemModule {}
