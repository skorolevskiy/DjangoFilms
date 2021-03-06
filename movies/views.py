from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.template.defaultfilters import lower
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, \
	DeleteView

from .models import Movie, Category, Actor, Genre, Rating
from .forms import ReviewForm, RatingForm


class GenreYear:
	"""Жанры и годы выхода фильмов"""

	def get_genres(self):
		return Genre.objects.all()

	def get_years(self):
		return Movie.objects.filter(draft=False).values("year").distinct().order_by('year')


class MovieView(GenreYear, ListView):
	"""Список фильмов"""
	model = Movie
	queryset = Movie.objects.filter(draft=False).order_by('-id')
	paginate_by = 2

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['star_form'] = RatingForm()
		return context


class MovieDetailView(GenreYear, DetailView):
	"""Подробно описание фильма"""
	model = Movie
	slug_field = 'url'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['star_form'] = RatingForm()
		context['form'] = ReviewForm()
		return context


class AddReview(View):
	"""Отзыв"""

	def post(self, request, pk):
		form = ReviewForm(request.POST)
		movie = Movie.objects.get(id=pk)
		if form.is_valid():
			form = form.save(commit=False)
			if request.POST.get("parent", None):
				form.parent_id = int(request.POST.get("parent"))
			form.movie = movie
			form.save()
		return redirect(movie.get_absolute_url())


class ActorView(GenreYear, DetailView):
	"""Информация о актере"""
	model = Actor
	template_name = 'movies/actor.html'
	slug_field = 'name'


class FilterMovieView(GenreYear, ListView):
	"""Фильтер фильмов"""
	paginate_by = 6

	def get_queryset(self):
		queryset = Movie.objects.filter(
			Q(year__in=self.request.GET.getlist("year")) |
			Q(genres__in=self.request.GET.getlist("genre"))
		).distinct().order_by('-id')
		return queryset

	def get_context_data(self, *args, **kwargs):
		context = super().get_context_data(*args, **kwargs)
		context['star_form'] = RatingForm()
		context["year"] = ''.join(
			[f"year={x}&" for x in self.request.GET.getlist("year")])
		context["genre"] = ''.join(
			[f"genre={x}&" for x in self.request.GET.getlist("genre")])
		return context


class JsonFilterMoviesView(ListView):
	"""Фильтр фильмов в json"""

	def get_queryset(self):
		queryset = Movie.objects.filter(
			Q(year__in=self.request.GET.getlist("year")) |
			Q(genres__in=self.request.GET.getlist("genre"))
		).distinct().values("title", "tagline", "url", "poster")
		return queryset

	def get(self, request, *args, **kwargs):
		queryset = list(self.get_queryset())
		return JsonResponse({"movies": queryset}, safe=False)


class AddStarRating(View):
	"""Добавление рейтинга фильму"""

	def get_client_ip(self, request):
		x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
		if x_forwarded_for:
			ip = x_forwarded_for.split(',')[0]
		else:
			ip = request.META.get('REMOTE_ADDR')
		return ip

	def post(self, request):
		form = RatingForm(request.POST)
		if form.is_valid():
			Rating.objects.update_or_create(
				ip=self.get_client_ip(request),
				movie_id=int(request.POST.get("movie")),
				defaults={'star_id': int(request.POST.get("star"))}
			)
			return HttpResponse(status=201)
		else:
			return HttpResponse(status=400)


class Search(GenreYear, ListView):
	"""Поиск фильмов"""
	paginate_by = 2

	def get_queryset(self):
		return Movie.objects.filter(title__contains=self.request.GET.get("q"))

	def get_context_data(self, *args, **kwargs):
		context = super().get_context_data(*args, **kwargs)
		context['star_form'] = RatingForm()
		context["q"] = f'q={self.request.GET.get("q")}&'
		return context


class CategoryView(GenreYear, ListView):
	"""Список фильмов"""
	model = Movie
	slug_field = 'url'

	def get_queryset(self):
		return Movie.objects.filter(category__url=self.kwargs['slug']).order_by('-id')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['star_form'] = RatingForm()
		return context
