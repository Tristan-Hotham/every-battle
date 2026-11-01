## Title

[OC] Every battle in history: 13,712 battles from Wikidata with a place and a date, 3001 BCE to 2026. The most fought-over region is Flanders (369 battles in 17 centuries), and Europe has 51% of all battles on 7% of the land

## Body

I took every Wikidata item that is an instance of "battle" or one of its subclasses (20,202 items) and mapped the 13,712 that have both coordinates and a date. The record is mostly recent: 52% of dated battles are after 1800, and the 19th century has the most (3,714). To compare places fairly I counted battles on an equal-area hexagon grid: the most fought-over region is Flanders, Artois and Brabant (Caesar, the Golden Spurs, Marlborough, Waterloo, Ypres), then western France (mostly the War in the Vendee, which French Wikipedia covers skirmish by skirmish), then the southern Levant. The hexagon around Jerusalem and Gaza has battles in 16 different centuries. Big caveat: this is a map of what Wikipedia editors have written up as much as of war. Europe has 51% of the mapped battles on 7% of the world's land, only 79% of the items are actually called a battle (the rest are sieges, raids, skirmishes and so on), and some famous fights such as the Siege of Leningrad are not typed as battles at all. Interactive map with a time slider: https://maps.tristanhotham.com/every-battle/

## Source comment

Sources: Wikidata (CC0), all items that are instances of battle (Q178561) or its subclasses, via the QLever SPARQL endpoint; English Wikipedia, List of battles by casualties (CC BY-SA 4.0); Natural Earth outlines (public domain).

Tools: Python (pandas, shapely, pyproj, matplotlib); Leaflet for the interactive map. Hexagons are on an equal-area grid in the Equal Earth projection.

Interactive version: https://maps.tristanhotham.com/every-battle/
Paper: {https://doi.org/10.5281/zenodo.23857870}
Blog post: {https://blog.tristanhotham.com/2026/10/31/every-battle/}
