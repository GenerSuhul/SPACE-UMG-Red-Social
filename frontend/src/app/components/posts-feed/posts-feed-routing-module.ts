import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { PostsFeed } from './posts-feed/posts-feed';

const routes: Routes = [
  { path: '', component: PostsFeed }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class PostsFeedRoutingModule {}
