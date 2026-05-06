import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { Config } from '../config/config';
import {
  ListPostsResponse,
  GetPostResponse,
  ListCommentsResponse,
  ListRepliesResponse,
  CreatePostResponse,
  CreateCommentResponse,
  ReactionResponse,
  DeleteResponse,
  ReactionType,
} from '../../models/posts';

@Injectable({ providedIn: 'root' })
export class PostsService {
  private readonly baseUrl: string;

  constructor(private http: HttpClient, private configService: Config) {
    this.baseUrl = `${this.configService.appConfig.apiUrl}/api/posts`;
  }

  // ---- Posts ----

  listPosts(page: number = 1, pageSize: number = 20): Observable<ListPostsResponse> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());
    return this.http.get<ListPostsResponse>(`${this.baseUrl}/`, { params });
  }

  getMyPosts(page: number = 1, pageSize: number = 20): Observable<ListPostsResponse> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());
    return this.http.get<ListPostsResponse>(`${this.baseUrl}/me`, { params });
  }

  getUserPosts(userId: string, page: number = 1, pageSize: number = 20): Observable<ListPostsResponse> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());
    return this.http.get<ListPostsResponse>(`${this.baseUrl}/user/${userId}`, { params });
  }

  getPostWithComments(postId: string): Observable<GetPostResponse> {
    return this.http.get<GetPostResponse>(`${this.baseUrl}/${postId}`);
  }

  createPost(content: string, image?: File): Observable<CreatePostResponse> {
    const fd = new FormData();
    fd.append('content', content);
    if (image) {
      fd.append('image', image);
    }
    return this.http.post<CreatePostResponse>(`${this.baseUrl}/`, fd);
  }

  deletePost(postId: string): Observable<DeleteResponse> {
    return this.http.delete<DeleteResponse>(`${this.baseUrl}/${postId}`);
  }

  // ---- Comments ----

  listComments(postId: string, page: number = 1, pageSize: number = 50): Observable<ListCommentsResponse> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());
    return this.http.get<ListCommentsResponse>(`${this.baseUrl}/${postId}/comments`, { params });
  }

  createComment(postId: string, content: string, parentCommentId?: string, image?: File): Observable<CreateCommentResponse> {
    const fd = new FormData();
    fd.append('content', content);
    if (parentCommentId) {
      fd.append('parent_comment_id', parentCommentId);
    }
    if (image) {
      fd.append('image', image);
    }
    return this.http.post<CreateCommentResponse>(`${this.baseUrl}/${postId}/comments`, fd);
  }

  listReplies(postId: string, commentId: string, page: number = 1, pageSize: number = 50): Observable<ListRepliesResponse> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());
    return this.http.get<ListRepliesResponse>(
      `${this.baseUrl}/${postId}/comments/${commentId}/replies`,
      { params },
    );
  }

  deleteComment(postId: string, commentId: string): Observable<DeleteResponse> {
    return this.http.delete<DeleteResponse>(`${this.baseUrl}/${postId}/comments/${commentId}`);
  }

  // ---- Reactions on posts ----

  reactToPost(postId: string, reactionType: ReactionType): Observable<ReactionResponse> {
    return this.http.post<ReactionResponse>(`${this.baseUrl}/${postId}/reactions`, {
      reaction_type: reactionType,
    });
  }

  removePostReaction(postId: string): Observable<DeleteResponse> {
    return this.http.delete<DeleteResponse>(`${this.baseUrl}/${postId}/reactions`);
  }

  // ---- Reactions on comments ----

  reactToComment(postId: string, commentId: string, reactionType: ReactionType): Observable<ReactionResponse> {
    return this.http.post<ReactionResponse>(
      `${this.baseUrl}/${postId}/comments/${commentId}/reactions`,
      { reaction_type: reactionType },
    );
  }

  removeCommentReaction(postId: string, commentId: string): Observable<DeleteResponse> {
    return this.http.delete<DeleteResponse>(
      `${this.baseUrl}/${postId}/comments/${commentId}/reactions`,
    );
  }
}
