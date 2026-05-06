import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { UsersManager } from './users-manager/users-manager';
import { MyFollows } from './my-follows/my-follows';
import { UserView } from './user-view/user-view';

const routes: Routes = [
  { path: '', component: UsersManager },
  { path: 'follows', component: MyFollows },
  { path: ':id', component: UserView },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class UsersRoutingModule {}
