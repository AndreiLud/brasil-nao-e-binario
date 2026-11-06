# Brief

## Goal

A complete, reproducible analysis of the Brazilian presidential elections of 2018, 2022 and 2026 (2014 as a baseline) and a static data story for GitHub Pages, written for a general audience in Brazilian Portuguese, with an English version (`docs/en/`) that shares the same data, charts and design.

## Thesis to test

Brazil is not split into two geographic blocks. Everywhere there are voters of both camps, plus people who voted for other candidates, voted blank or null, or did not vote. The "winner by city" map hides that mixture. The data are shown without forcing the thesis: where they contradict it (region, income), the site says so with the same weight.

## Audience and tone

Anyone, no data background. Short sentences, journalistic Portuguese, neutral: same tone, space and type of language for both camps, no evaluative adjectives, no opinions, no predictions. Municipal data are described as associations, never as individual behaviour.

## Questions

1. National result from 2018 to 2026, both rounds, including abstention, blank and null votes.
2. Result of every municipality in every election and round.
3. How mixed the vote is: distribution of municipal shares, municipalities where the local loser got more than 30% and 40%, absolute votes of each camp by region.
4. Where and how much the bolsonarista camp grew in 2018 (against the non-PT side of 2014).
5. Where the lulista camp regained ground in 2022.
6. How the 2026 runoff turnaround happened, and how it is associated with third-candidate votes and turnout change.
7. How the vote is associated with municipality size, region and income.

## Chapters of the site

1. The question, with one strong number.
2. Three elections in one minute (national results over the whole electorate).
3. The map that misleads (winner, then proportion, then dots; then free exploration).
4. Nobody lives in a bubble (distribution, regions, extremes, income, size and region).
5. 2018.
6. 2022.
7. 2026, the turnaround.
8. Your city (search, "100 voters" view for every election).
9. How we did it.

## Design decisions

* Palette: lulista camp violet, bolsonarista camp ochre, the mixture a light rosé (the perceptual blend of the two), neutral greys for third candidates, blank/null and non-voters. Chosen to avoid party colors (red, the flag's green and yellow, blue) and checked under protanopia, deuteranopia and tritanopia simulation. Maps sit on a dark stage, where the mixed places stand out. Change maps use a neutral grey middle ("no change").
* Type: Fraunces (headlines) and Inter (text, tabular figures in tables), self-hosted.
* Stack: plain HTML, CSS and JavaScript; D3 modules, topojson-client and Scrollama vendored with pinned versions; canvas for the dense map layers.
