import { NgModule } from '@angular/core';
import { SharedImportModule } from '../../shared-import/shared-import-module';
import { PostsFeedRoutingModule } from './posts-feed-routing-module';
import { PostItemModule } from './post-item/post-item-module';
import { PostsFeed } from './posts-feed/posts-feed';

@NgModule({
  declarations: [PostsFeed],
  imports: [
    SharedImportModule,
    PostsFeedRoutingModule,
    PostItemModule,
  ],
})
export class PostsFeedModule {}
