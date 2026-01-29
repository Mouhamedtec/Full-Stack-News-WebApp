import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { finalize } from 'rxjs';
import { NewsService, Article, NewsResponse } from '../news';

@Component({
  selector: 'app-news-list',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './news-list.html',
  styleUrl: './news-list.scss',
})
export class NewsList implements OnInit {
  protected readonly categories = [
    'business',
    'entertainment',
    'general',
    'health',
    'science',
    'sports',
    'technology',
  ];

  protected readonly languages = [
    'ar', 'en', 'cn', 'de', 'es', 'fr', 'he', 'it', 'nl', 'no', 'pt', 'ru', 'sv', 'se', 'ud', 'zh', 'en-US'
  ];

  protected readonly countries = [
    'ae', 'ar', 'at', 'au', 'be', 'bg', 'br', 'ca', 'ch', 'cn', 'co', 'cu', 'cz', 'de', 'eg', 'es', 'fr',
    'gb', 'gr', 'hk', 'hu', 'id', 'ie', 'il', 'in', 'is', 'it', 'jp', 'kr', 'lt', 'lv', 'ma', 'mx', 'my',
    'ng', 'nl', 'no', 'nz', 'ph', 'pk', 'pl', 'pt', 'ro', 'rs', 'ru', 'sa', 'se', 'sg', 'si', 'sk', 'th',
    'tr', 'tw', 'ua', 'us', 've', 'za', 'zh'
  ];

  protected readonly sortOptions = [
    { value: 'recent', label: 'Most recent' },
    { value: 'oldest', label: 'Oldest' },
    { value: 'title', label: 'Title A–Z' },
  ];

  protected readonly pageSize = 50;
  protected page = 1;
  protected totalPages = 1;
  protected totalResults = 0;
  protected articles: Article[] = [];
  protected loading = false;
  protected error: string | null = null;
  protected nextUrl: string | null = null;
  protected previousUrl: string | null = null;

  protected readonly form = new FormGroup({
    search: new FormControl('', { nonNullable: true }),
    category: new FormControl('', { nonNullable: true }),
    source: new FormControl('', { nonNullable: true }),
    author: new FormControl('', { nonNullable: true }),
    user_language: new FormControl('', { nonNullable: true }),
    user_country_code: new FormControl('', { nonNullable: true }),
    date_from: new FormControl('', { nonNullable: true }),
    date_to: new FormControl('', { nonNullable: true }),
    sort_by: new FormControl<'recent' | 'oldest' | 'title'>('recent', { nonNullable: true }),
  });

  constructor(private readonly newsService: NewsService) {}

  ngOnInit(): void {
    this.fetchNews();
  }

  protected applyFilters(): void {
    this.page = 1;
    this.fetchNews();
  }

  protected resetFilters(): void {
    this.form.reset({
      search: '',
      category: '',
      source: '',
      author: '',
      user_language: '',
      user_country_code: '',
      date_from: '',
      date_to: '',
      sort_by: 'recent',
    });
    this.page = 1;
    this.fetchNews();
  }

  protected nextPage(): void {
    if (this.loading) {
      return;
    }

    const nextPage = this.getPageFromUrl(this.nextUrl);
    if (nextPage) {
      this.page = nextPage;
      this.fetchNews();
      return;
    }

    if (this.page < this.totalPages) {
      this.page += 1;
      this.fetchNews();
    }
  }

  protected previousPage(): void {
    if (this.loading) {
      return;
    }

    const prevPage = this.getPageFromUrl(this.previousUrl);
    if (prevPage) {
      this.page = prevPage;
      this.fetchNews();
      return;
    }

    if (this.page > 1) {
      this.page -= 1;
      this.fetchNews();
    }
  }

  private fetchNews(): void {
    const formValue = this.form.getRawValue();

    const query = {
      ...formValue,
      date_from: this.toIsoString(formValue.date_from),
      date_to: this.toIsoString(formValue.date_to),
      page: this.page,
    };

    this.loading = true;
    this.error = null;

    this.newsService
      .getNews(query)
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: (response: NewsResponse) => {
          const normalized = response as NewsResponse | Article[];
          const results = Array.isArray(normalized)
            ? normalized
            : (normalized.results ?? []);

          const totalCount = Array.isArray(normalized)
            ? normalized.length
            : normalized.count;

          this.nextUrl = Array.isArray(normalized) ? null : normalized.next;
          this.previousUrl = Array.isArray(normalized) ? null : normalized.previous;

          const effectivePageSize = Array.isArray(normalized)
            ? normalized.length
            : (normalized.results?.length || this.pageSize);

          this.totalResults = totalCount ?? 0;
          this.totalPages = Math.max(1, Math.ceil(this.totalResults / Math.max(1, effectivePageSize)));
          this.articles = results;
        },
        error: () => {
          this.error = 'We could not load the latest headlines. Please try again.';
        },
      });
  }

  private toIsoString(value: string): string | undefined {
    if (!value) {
      return undefined;
    }

    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
      return value;
    }

    return parsed.toISOString();
  }

  private getPageFromUrl(url: string | null): number | null {
    if (!url) {
      return null;
    }

    try {
      const parsed = new URL(url);
      const pageParam = parsed.searchParams.get('page');
      if (!pageParam) {
        return null;
      }

      const pageValue = Number(pageParam);
      return Number.isFinite(pageValue) && pageValue > 0 ? pageValue : null;
    } catch {
      return null;
    }
  }
}
