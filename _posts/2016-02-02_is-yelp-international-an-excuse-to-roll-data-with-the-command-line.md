# Is Yelp international? — An excuse to roll data with the command line

The recent Capstone project in the [Coursera Data Science Specilization](https://www.coursera.org/specializations/jhu-data-science) was based on the [Yelp Dataset Challenge Round 6](http://www.yelp.com/dataset_challenge). As this specialization made me gain one major understanding — that I should do anything I can to avoid using R if I don’t want to go mad — I was eager to explore this dataset with only using the command line. Although my practice is not exactly what Jeroen Janssens rolls, I strongly recommend his book, [Data Science at the Command Line](http://datascienceatthecommandline.com/), as an intro on the domain.

In our [daily data practice](http://www.slideshare.net/soobrosa/6w-bp-datashow) we rely on pretty oldschool technologies, like makefiles, bash and SQL, so I set out to try to test the limits of Unix commands, pipes and some special, self-contained tools, three of them altogether slightly bigger than 1 Mbyte. I believe getting to know in detail how this equipment work could be a better investment of yours.

I will use the following specimens:

* [json2csv](https://github.com/jehiah/json2csv) (“converts a stream of newline separated json data to csv format”),
* [jq](https://stedolan.github.io/jq/) (“*sed* for JSON data — you can use it to slice and filter and map and transform structured data with the same ease that *sed, awk, grep* and friends let you play with text”),
* [q](http://harelba.github.io/q/) (“allows direct execution of SQL-like queries on CSVs/TSVs”),
* [Rio](https://github.com/jeroenjanssens/data-science-at-the-command-line/blob/master/tools/Rio) (turns CSV to CSV or PNG via R),
* [miller](https://github.com/johnkerl/miller) (“*sed, awk, cut, join,* and *sort* for name-indexed data such as CSV”)
“Not unlike jq for JSON, Miller is written in modern C, and it has zero runtime dependencies. You can download or compile a single binary, scp it to a faraway machine, and expect it to work.” ([Source](https://github.com/johnkerl/miller))

I’m slightly familiar with the domain as some years ago I’ve written [my thesis](http://issuu.com/soobrosa/docs/soobrosa_thesis?e=0) on the touristic effect of the location-based community activities in Hungary — it was a critical comparison of geocaching and Foursquare. I realised how much I got used to use both Foursquare and Yelp living in Germany. The German Qype sold to Yelp in 2012. Did this acquisition make Yelp international? Can we tell from the data whether this deal was worth it for Yelp? Based on the user generated contect metrics, not really.

# Blink that cursor

Let’s shape the dataset to be explorable. For reproducability a [Makefile](https://gist.github.com/soobrosa/4adf89ce197eb6299eb9) is the best. Below I focus on the actual analysis, you can find more simple practicalities in the Makefile — like how to pretty print a JSON, how to get a random sample and so.

Let’s start with flattening lazily the JSONs to CSVs. For simpler cases [json2csv](https://github.com/jehiah/json2csv) is enough while [jq](http://stedolan.github.io/jq/) is your weapon to roll complex logic.

```
#
# -p=true means "print csv header row"
#
# -c stands for "put each JSON object on a single line"
#

$ < source/yelp_academic_dataset_tip.json | json2csv -p=true -k business_id,date,likes,user_id > source_flattened/tip_no_text.csv
$ < source/yelp_academic_dataset_review.json | json2csv -p=true -k business_id,date,review_id,stars,user_id > source_flattened/review_compact_no_text.csv
$ < source/yelp_academic_dataset_business.json | jq -c ‘{business_id, category_main: .categories[0], category_sub: .categories[1], city, latitude, longitude, name, neighborhood: .neighborhoods[0], open, review_count, stars, state}’ | json2csv -p=true -k business_id,category_main,category_sub,city,latitude,longitude,name,neighborhood,open,review_count,stars,state > source_flattened/business.csv
```

Now that we have the data in CSVs, let’s query them in SQL with the help of [q](http://harelba.github.io/q/). I counted the number of businesses per state and tried to get an estimate of their population from Wikipedia.

```
#
# -H skips header row
# -d, defines "," as delimiter
#

$ ./q -H -d, \
" SELECT state, COUNT(*)
  FROM business.csv
  GROUP BY 1
  HAVING COUNT(*) > 100
  ORDER BY 2 DESC "

AZ,25230   --  Phoenix, AZ — capital, 1.5 m
NV,16485   --  Las Vegas, NV — largest in state, 0.6 m
NC,4963    --  Charlotte, NC — largest in state, 0.8 m
QC,3921    --  Montreal — largest, 1.6 m
PA,3041    --  Pittsburgh, PA — 0.3 m
EDH,2971   --  Edinburgh, UK — capital — 0.5 m
WI,2307    --  Madison, WI — 0.006 m
BW,934     --  Karlsruhe — 0.3 m
IL,627     --  Urbana-Champaign, IL — 0.003 m
ON,351     --  Waterloo
SC,189     --  Fort Mill == Charlotte, NC
MLN,123    --  Edinburgh, UK
```

I have chosen a small, a midsized and a larger city from both the US and abroad with almost equal population. I calculated the reviewing and tipping activity trends in the three segments.

```
# US:
# + AZ,25230   --  Phoenix, AZ — capital, 1.5 m
# + NV,16485   --  Las Vegas, NV — largest, 0.6 m
# + PA,3041    --  Pittsburgh, PA — 0.3 m
# Control:
# + QC,3921    --  Montreal — largest, 1.6 m
# + EDH,2971   --  Edinburgh, UK — capital — 0.5 m
# + MLN,123    --  Edinburgh, UK
# + BW,934     --  Karlsruhe — 0.3 m
#
# -H outputs header line
#

$ ./q -H -O -d, \
" SELECT business_id, date, COUNT(*) AS reviews
  FROM review_compact_no_text.csv
  GROUP BY 1, 2 " \
> temp1.csv
 
$ ./q -H -O -d, \
" SELECT t.date,
  CASE WHEN b.state IN (‘AZ’, ‘NV’, ‘PA’) THEN ‘USA’
  WHEN b.state IN (‘QC’, ‘EDH’, ‘MLN’, ‘BW’) THEN ‘Control’
  ELSE ‘Others’ END AS state,
  SUM(t.reviews) AS reviews
  FROM temp1.csv AS t
  JOIN business.csv AS b
  ON (t.business_id = b.business_id)
  GROUP BY 1, 2
  ORDER BY 2, 1 " \
> reviews_summed.csv

$ ./q -H -O -d, \
" SELECT business_id, date, COUNT(*) AS tips
  FROM tip_no_text.csv
  GROUP BY 1, 2 " \
> temp2.csv

$ ./q -H -O -d, \
" SELECT t.date,
  CASE WHEN b.state IN (‘AZ’, ‘NV’, ‘PA’) THEN ‘USA’
  WHEN b.state IN (‘QC’, ‘EDH’, ‘MLN’, ‘BW’) THEN ‘Control’
  ELSE ‘Others’ END AS state,
  SUM(t.tips) AS tips
  FROM temp2.csv AS t
  JOIN business.csv AS b
  ON (t.business_id = b.business_id)
  GROUP BY 1, 2
  ORDER BY 2, 1 " \
> tips_summed.csv
```

# Show and tell

As in production or on the call let’s use a visual clue whether a linear correlation will be enough to say something most likely. [Rio](https://github.com/jeroenjanssens/data-science-at-the-command-line/blob/master/tools/Rio) from Jeroen is the smallest possible interface to abuse R to draw charts. Don’t forget that you have to have R installed. On OSX you might struggle a bit to get it work this combination helped me:

```
$ brew reinstall — with-libtiff — ignore-dependencies — with-x11 imagemagick
$ sudo cp /opt/X11/lib/libfreetype.6.dylib /usr/local/lib/libfreetype.6.dylib
```

Charting the change of user generated content does not show a rosy picture. The non-US control is way less productive than the US group.

```
$ < reviews_summed.csv ../Rio.sh -ge 'g+geom_line(aes(x=as.Date(date), y=reviews, group=state, color=state)) + labs(x="Year", title="Reviewing activity trends in three segments")' | display
```

<img src="https://cdn-images-1.medium.com/max/800/1*Ds8CLx1sn9FvXkHDhUdRQQ.png" alt="">

```
$ < tips_summed.csv ../Rio.sh -ge 'g+geom_line(aes(x=as.Date(date), y=tips, group=state, color=state)) + labs(x="Year", title="Tipping activity trends in three segments")' | display
```

<img src="https://cdn-images-1.medium.com/max/800/1*nRrMa3xbF7snDTKIGLvCSw.png" alt="">

Based on the reviews and tips timeline it’s inevitable that the control grows much slower and no specific uptick happened at the acquisition. You might say having Las Vegas skews the sample, but that could be a good starting exercise to check the dataset without it. :) Also if you got the taste, don’t stop here! It’s fairly easy to roll deeper statistical analysis like with [miller](https://github.com/johnkerl/miller):

```
$ ./q -H -O -d, \
" SELECT strftime('%Y%m%d',date) AS date, \
  state, \
  reviews \
  FROM reviews_summed.csv " \
> temp3.csv

$ cat temp3.csv | ./mlr --csv --rs lf --opprint \
  stats2 -a linreg-pca -f date,reviews -g state

state date_reviews_pca_m date_reviews_pca_b date_reviews_pca_n date_reviews_pca_quality
Control 0.000804 -16137.212616 2516 0.999999
Others 0.001528 -30670.842174 3173 0.999999
USA 0.012803 -256934.209362 3399 0.999974
```

Have fun with data on the command line and don’t look back in anger at IDEs!