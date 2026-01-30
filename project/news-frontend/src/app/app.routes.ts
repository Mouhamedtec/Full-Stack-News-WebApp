import { Routes } from '@angular/router';
import { NewsList } from './news/news-list/news-list';

export const routes: Routes = [
	{ path: '', component: NewsList },
	{ path: '**', redirectTo: '' },
];
