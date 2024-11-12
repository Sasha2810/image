import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import numpy as np

class GetFaeatures:
    def __init__():
        pass

    # geopandas distance 
    def add_distance_feature(df):
        # Создаем геометрические точки для pickup и dropoff
        df['pickup_point'] = df.apply(lambda row: Point(row['pickup_longitude'], row['pickup_latitude']), axis=1)
        df['dropoff_point'] = df.apply(lambda row: Point(row['dropoff_longitude'], row['dropoff_latitude']), axis=1)

        # Создаем GeoDataFrame для pickup и dropoff
        pickup_points = gpd.GeoDataFrame(df, geometry='pickup_point', crs="EPSG:4326")
        dropoff_points = gpd.GeoDataFrame(df, geometry='dropoff_point', crs="EPSG:4326")

        # Преобразуем в EPSG:2263
        pickup_points = pickup_points.to_crs(epsg=2263)
        dropoff_points = dropoff_points.to_crs(epsg=2263)ч

        # Вычисляем расстояние и добавляем в DataFrame
        df['distance_geo_km'] = round(pickup_points.geometry.distance(dropoff_points.geometry) / 1000, 2)

        return df 
    
    # evklid distance
    def add_euclidean_distance_feature(df):
        # Константа для перевода широты в метры
        lat_to_m = 111320  # в метрах

        # Вычисляем среднюю широту для коррекции долготы
        avg_lat = np.radians((df['pickup_latitude'] + df['dropoff_latitude']) / 2)
        lon_to_m = lat_to_m * np.cos(avg_lat)

        # Вычисляем разницу широт и долгот в метрах
        dlat_m = (df['dropoff_latitude'] - df['pickup_latitude']) * lat_to_m
        dlon_m = (df['dropoff_longitude'] - df['pickup_longitude']) * lon_to_m

        # Вычисляем Евклидово расстояние в метрах и добавляем новую колонку с расстоянием в километрах
        df['evklid_distance_km'] = round(np.sqrt(dlat_m**2 + dlon_m**2) / 1000, 2)

        return df
    
    # растояние по кварталам
    def add_manhattan_distance_feature(df):
        # Вычисляем манхэттенское расстояние в метрах
        manhattan_distance_m = (
            np.abs(df['dropoff_latitude'] - df['pickup_latitude']) * 111320 +  # Разница по широте
            np.abs(df['dropoff_longitude'] - df['pickup_longitude']) * (111320 * np.cos(np.radians((df['pickup_latitude'] + df['dropoff_latitude']) / 2)))  # Разница по долготе
        )
        
        # Добавляем новую колонку с расстоянием в километрах
        df['manhattan_distance_km'] = round(manhattan_distance_m / 1000, 2)

        return df
    
    # растояние по кварталам
    def add_distances_to_top_places(df):
        """
        Добавляет расстояния от точек pickup и dropoff до популярных мест в Нью-Йорке.
        
        :param df: DataFrame с колонками 'pickup_longitude', 'pickup_latitude', 
                    'dropoff_longitude', 'dropoff_latitude'.
        :return: Обновленный DataFrame с колонками расстояний до популярных мест.
        """
        
        # Координаты популярных мест
        top_places = {
            "Statue of Liberty": (40.6892, -74.0445),
            "Central Park": (40.7851, -73.9683),
            "Empire State Building": (40.748817, -73.985428),
            "MoMA": (40.761436, -73.977621),
            "Times Square": (40.7580, -73.9855)
        }

        # Создаем GeoDataFrame для pickup и dropoff
        pickup_points = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['pickup_longitude'], df['pickup_latitude']), crs="EPSG:4326")
        dropoff_points = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['dropoff_longitude'], df['dropoff_latitude']), crs="EPSG:4326")

        # Преобразуем в EPSG:2263
        pickup_points = pickup_points.to_crs(epsg=2263)
        dropoff_points = dropoff_points.to_crs(epsg=2263)

        # Вычисляем расстояния до популярных мест
        for place_name, (lat, lon) in top_places.items():
            # Создаем точку для места
            place_point = Point(lon, lat)  # Долгота, широта
            place_gdf = gpd.GeoDataFrame(geometry=[place_point], crs='EPSG:4326').to_crs(epsg=2263)

            # Вычисляем расстояние от pickup и dropoff до места
            pickup_distance = pickup_points.distance(place_gdf.geometry[0])
            dropoff_distance = dropoff_points.distance(place_gdf.geometry[0])

            # Добавляем новые колонки с расстоянием в километрах
            df[f'distance_to_{place_name.replace(" ", "_").lower()}_from_pickup_km'] = round(pickup_distance / 1000, 2)
            df[f'distance_to_{place_name.replace(" ", "_").lower()}_from_dropoff_km'] = round(dropoff_distance / 1000, 2)

        return df
    
    # время дня
    def time_of_day(df, time_column):
        """
        Добавляет категориальную колонку 'time_of_day' в DataFrame на основе временной метки.

        :param df: DataFrame с временной меткой
        :param time_column: Название колонки с временной меткой
        :return: Обновленный DataFrame с новой колонкой 'time_of_day'
        """
        
        # Преобразуем колонку времени в datetime, если это еще не сделано
        df[time_column] = pd.to_datetime(df[time_column])

        # Определяем функцию для классификации времени суток
        def classify_time(hour):
            if 5 <= hour < 12:
                return 'Утро'
            elif 12 <= hour < 18:
                return 'День'
            elif 18 <= hour < 22:
                return 'Вечер'
            else:
                return 'Ночь'

        # Применяем функцию к часам из временной метки
        df['time_of_day'] = df[time_column].dt.hour.apply(classify_time)

        return df
    
    # сезон
    def add_season_feature(df, date_column):
        """
        Добавляет категориальную колонку 'season' в DataFrame на основе даты.

        :param df: DataFrame с колонкой с датой
        :param date_column: Название колонки с датой
        :return: Обновленный DataFrame с новой колонкой 'season'
        """
        
        # Преобразуем колонку даты в datetime, если это еще не сделано
        df[date_column] = pd.to_datetime(df[date_column])

        # Определяем функцию для классификации времени года
        def classify_season(date):
            if (date >= pd.Timestamp(date.year, 3, 21)) and (date < pd.Timestamp(date.year, 6, 21)):
                return 'Весна'
            elif (date >= pd.Timestamp(date.year, 6, 21)) and (date < pd.Timestamp(date.year, 9, 23)):
                return 'Лето'
            elif (date >= pd.Timestamp(date.year, 9, 23)) and (date < pd.Timestamp(date.year, 12, 21)):
                return 'Осень'
            else:
                return 'Зима'

        # Применяем функцию к каждому элементу в колонке даты
        df['season'] = df[date_column].apply(classify_season)

        return df

class FeatureAdder:
    def __init__(self, df):
        self.df = df
        self.nyc = (40.724944, -74.001541)  # Координаты центра Нью-Йорка
        self.jfk = (40.645494, -73.785937)  # Координаты аэропорта JFK
        self.lga = (40.774071, -73.872067)  # Координаты аэропорта LGA
        self.nla = (40.690764, -74.177721)  # Координаты аэропорта NLA

    def distance(self, lat1, lon1, lat2, lon2):
        """Вычисляет расстояние между двумя точками по их координатам."""
        # Здесь можно использовать более точную формулу (например, haversine)
        return np.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)

    def add_distance_feature(self):
        """Добавляет общий признак расстояния между точками забора и высадки."""
        self.df['distance'] = self.distance(
            self.df['pickup_latitude'], 
            self.df['pickup_longitude'], 
            self.df['dropoff_latitude'], 
            self.df['dropoff_longitude']
        )

    def add_time_features(self):
        """Добавляет временные признаки из столбца pickup_datetime."""
        self.df['pickup_datetime'] = pd.to_datetime(self.df['pickup_datetime'], format="%Y-%m-%d %H:%M:%S UTC")
        self.df['hour'] = self.df['pickup_datetime'].dt.hour
        self.df['day'] = self.df['pickup_datetime'].dt.day
        self.df['month'] = self.df['pickup_datetime'].dt.month
        self.df['year'] = self.df['pickup_datetime'].dt.year
        self.df.drop('pickup_datetime', axis=1, inplace=True)

    def add_distance_to_airports(self):
        """Добавляет признаки расстояния до аэропортов и центра города."""
        # Расстояние до центра города
        self.df['pickup_distance_to_center'] = self.distance(
            self.nyc[0], 
            self.nyc[1], 
            self.df['pickup_latitude'], 
            self.df['pickup_longitude']
        )
        self.df['dropoff_distance_to_center'] = self.distance(
            self.nyc[0], 
            self.nyc[1], 
            self.df['dropoff_latitude'], 
            self.df['dropoff_longitude']
        )

        # Расстояние до аэропорта JFK
        self.df['pickup_distance_to_jfk'] = self.distance(
            self.jfk[0], 
            self.jfk[1], 
            self.df['pickup_latitude'], 
            self.df['pickup_longitude']
        )
        self.df['dropoff_distance_to_jfk'] = self.distance(
            self.jfk[0], 
            self.jfk[1], 
            self.df['dropoff_latitude'], 
            self.df['dropoff_longitude']
        )

        # Расстояние до аэропорта LGA
        self.df['pickup_distance_to_lga'] = self.distance(
            self.lga[0], 
            self.lga[1], 
            self.df['pickup_latitude'], 
            self.df['pickup_longitude']
        )
        self.df['dropoff_distance_to_lga'] = self.distance(
            self.lga[0], 
            self.lga[1], 
            self.df['dropoff_latitude'], 
            self.df['dropoff_longitude']
        )

        # Расстояние до аэропорта NLA
        self.df['pickup_distance_to_nla'] = self.distance(
            self.nla[0], 
            self.nla[1], 
            self.df['pickup_latitude'], 
            self.df['pickup_longitude']
        )
        self.df['dropoff_distance_to_nla'] = self.distance(
            self.nla[0], 
            self.nla[1], 
            self.df['dropoff_latitude'], 
            self.df['dropoff_longitude']
        )

    def add_coordinate_differences(self):
        """Добавляет абсолютные разности по координатам между точками забора и высадки."""
        self.df['abs_long_diff'] = np.abs(self.df.dropoff_longitude - self.df.pickup_longitude)
        self.df['abs_lat_diff'] = np.abs(self.df.dropoff_latitude - self.df.pickup_latitude)

    def add_all_features(self):
        """Добавляет все признаки в DataFrame."""
        print("Adding distance feature...")
        self.add_distance_feature()
        
        print("Adding time features...")
        self.add_time_features()
        
        print("Adding distance to airports...")
        self.add_distance_to_airports()
        
        print("Adding coordinate differences...")
        self.add_coordinate_differences()

# Пример использования
# df - ваш DataFrame с данными о поездках такси
# feature_adder = FeatureAdder(df)
# feature_adder.add_all_features()