import { NgModule } from '@angular/core';
import { SharedImportModule } from '../../shared-import/shared-import-module';
import { PostsFeedRoutingModule } from './posts-feed-routing-module';
import { PostsFeed } from './posts-feed/posts-feed';
import { PostItem } from './post-item/post-item';

@NgModule({
  declarations: [
    PostsFeed,
    PostItem,
  ],
  imports: [
    SharedImportModule,
    PostsFeedRoutingModule,
  ],
})
export class PostsFeedModule {}
