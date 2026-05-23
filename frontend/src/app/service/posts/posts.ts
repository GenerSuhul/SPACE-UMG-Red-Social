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
  UpdatePostResponse,
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

  listReels(page: number = 1, pageSize: number = 20): Observable<ListPostsResponse> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString())
      .set('type', 'reel');
    return this.http.get<ListPostsResponse>(`${this.baseUrl}/`, { params });
  }

  listStories(page: number = 1, pageSize: number = 20): Observable<ListPostsResponse> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString())
      .set('type', 'story');
    return this.http.get<ListPostsResponse>(`${this.baseUrl}/`, { params });
  }

  createReel(content: string, videoUrl: string): Observable<CreatePostResponse> {
    const fd = new FormData();
    fd.append('content', content);
    fd.append('type', 'reel');
    fd.append('media_urls', videoUrl);
    return this.http.post<CreatePostResponse>(`${this.baseUrl}/`, fd);
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

  createPost(content: string, files: File[] = [], mediaUrls: string[] = [], type: string = 'post'): Observable<CreatePostResponse> {
    if ((mediaUrls && mediaUrls.length > 0) || files.length === 0) {
      return this.http.post<CreatePostResponse>(`${this.baseUrl}/`, {
        content,
        type,
        media_urls: mediaUrls
      });
    }
    const fd = new FormData();
    fd.append('content', content);
    fd.append('type', type);
    files.forEach(f => fd.append('images', f));
    return this.http.post<CreatePostResponse>(`${this.baseUrl}/`, fd);
  }

  updatePost(postId: string, content?: string, files?: File[], clearImages = false, mediaUrls?: string[]): Observable<UpdatePostResponse> {
    if (clearImages) {
      const body: Record<string, unknown> = { images: [] };
      if (content !== undefined) body['content'] = content;
      if (mediaUrls !== undefined) body['media_urls'] = mediaUrls;
      return this.http.patch<UpdatePostResponse>(`${this.baseUrl}/${postId}`, body);
    }
    if (mediaUrls !== undefined) {
      const body: Record<string, unknown> = { media_urls: mediaUrls };
      if (content !== undefined) body['content'] = content;
      return this.http.patch<UpdatePostResponse>(`${this.baseUrl}/${postId}`, body);
    }
    const fd = new FormData();
    if (content !== undefined) fd.append('content', content);
    files?.forEach(f => fd.append('images', f));
    return this.http.patch<UpdatePostResponse>(`${this.baseUrl}/${postId}`, fd);
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

  createComment(postId: string, content: string, parentCommentId?: string, image?: File, imageUrl?: string): Observable<CreateCommentResponse> {
    if (imageUrl || !image) {
      const body: Record<string, unknown> = { content };
      if (parentCommentId) body['parent_comment_id'] = parentCommentId;
      if (imageUrl) body['image_url'] = imageUrl;
      return this.http.post<CreateCommentResponse>(`${this.baseUrl}/${postId}/comments`, body);
    }
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
