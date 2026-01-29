import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environments';

export interface Article {
  id: number;
  title: string;
  content_preview: string;
  url: string;
  category: string;
  source: string;
  author: string | null;
  url_to_image: string | null;
  published_date: string;
}

export interface NewsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Article[];
}

export interface NewsQuery {
  search?: string;
  category?: string;
  source?: string;
  author?: string;
  user_language?: string;
  user_country_code?: string;
  date_from?: string;
  date_to?: string;
  sort_by?: 'recent' | 'oldest' | 'title';
  page?: number;
}

@Injectable({
  providedIn: 'root',
})
export class NewsService {
  private readonly baseUrl = `${environment.apiBaseUrl}/api/news/`;

  constructor(private readonly http: HttpClient) {}

  getNews(query: NewsQuery): Observable<NewsResponse> {
    let params = new HttpParams();

    Object.entries(query).forEach(([key, value]) => {
      if (value === undefined || value === null || value === '') {
        return;
      }

      params = params.set(key, String(value));
    });

    return this.http.get<NewsResponse>(this.baseUrl, { params });
  }
}
