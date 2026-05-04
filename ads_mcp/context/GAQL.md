# Google Ads Query Language (GAQL)

## Query Grammar

Here is the Google Ads Query Language grammar reference (in regular expression notation):

```
Query            -> SelectClause FromClause WhereClause? OrderByClause?
                    LimitClause? ParametersClause?
SelectClause     -> SELECT FieldName (, FieldName)*
FromClause       -> FROM ResourceName
WhereClause      -> WHERE Condition (AND Condition)*
OrderByClause    -> ORDER BY Ordering (, Ordering)*
LimitClause      -> LIMIT PositiveInteger
ParametersClause -> PARAMETERS Literal = Value (, Literal = Value)*

Condition        -> FieldName Operator Value
Operator         -> = | != | > | >= | < | <= | IN | NOT IN |
                    LIKE | NOT LIKE | CONTAINS ANY | CONTAINS ALL |
                    CONTAINS NONE | IS NULL | IS NOT NULL | DURING |
                    BETWEEN | REGEXP_MATCH | NOT REGEXP_MATCH
Value            -> Literal | LiteralList | Number | NumberList | String |
                    StringList | Function
Ordering         -> FieldName (ASC | DESC)?

FieldName        -> [a-z] ([a-zA-Z0-9._])*
ResourceName     -> [a-z] ([a-zA-Z_])*

StringList       -> ( String (, String)* )
LiteralList      -> ( Literal (, Literal)* )
NumberList       -> ( Number (, Number)* )

PositiveInteger  -> [1-9] ([0-9])*
Number           -> -? [0-9]+ (. [0-9] [0-9]*)?
String           -> (' Char* ') | (" Char* ")
Literal          -> [a-zA-Z0-9_]*

Function         -> LAST_14_DAYS | LAST_30_DAYS | LAST_7_DAYS |
                    LAST_BUSINESS_WEEK | LAST_MONTH | LAST_WEEK_MON_SUN |
                    LAST_WEEK_SUN_SAT | THIS_MONTH | THIS_WEEK_MON_TODAY |
                    THIS_WEEK_SUN_TODAY | TODAY | YESTERDAY
```

- ? indicates an optional element
- \* means zero or more; + means one or more
- (xxxxxx) indicates a grouping
- [a-z0-9] signifies character ranges
- | stands for "or"

### Rules and limitations
The `REGEXP_MATCH` operator uses RE2 syntax.

To match a literal [, ], %, or _ using the `LIKE` operator, surround the character in square brackets. For example, the following condition matches all campaign.name values that start with [Earth_to_Mars]:

```
campaign.name LIKE '[[]Earth[_]to[_]Mars[]]%'
```

The `LIKE` operator can only be used on a string field, not an array.

## Query Structure

Queries for resource, segment, and metric fields can be sent to Google Ads Service. To construct a query in Google Ads Query Language, you will need to build it using the language grammar. A query is made up of a number of clauses:

*   `SELECT`
*   `FROM`
*   `WHERE`
*   `ORDER BY`
*   `LIMIT`
*   `PARAMETERS`

Clauses use _field names_, _resource names_, _operators_, _conditions_, and _orderings_ to help you select the correct data. When combined into a single query, a request can be made using Google Ads API.

### Clauses

#### SELECT

The `SELECT` clause specifies a set of fields to fetch in the request. `SELECT` takes a comma-separated list of resource fields, segment fields, and metrics, returning the values in the response. The `SELECT` clause is **required** in a query.

The sample query below shows an example of selecting attributes for a given resource:

```
SELECT
    campaign.id,
    campaign.name
FROM campaign
```

You can request different field types in a single request, for example:

```
SELECT
    campaign.id,
    campaign.name,
    bidding_strategy.id,
    bidding_strategy.name,
    segments.device,
    segments.date,
    metrics.impressions,
    metrics.clicks
FROM campaign
WHERE segments.date DURING LAST_30_DAYS
```

*   Resource fields
    *   `campaign.id`
    *   `campaign.name`
*   Resource fields
    *   `bidding_strategy.id`
    *   `bidding_strategy.name`
*   Segment fields
    *   `segments.device`
    *   `segments.date`
*   Metrics
    *   `metrics.impressions`
    *   `metrics.clicks`

Some fields may not be allowed in the `SELECT` clause, due to the following restrictions:

*   Querying fields that are not selectable. These fields will have their `Selectable` metadata attribute marked as `false`.
*   Selecting attributes of repeated fields. These fields will have their `isRepeated` metadata attribute marked as `true`.
*   Selecting fields that are not available for the given resource in the `FROM` clause. Attributes of some resources cannot be selected together, also only a subset of all metrics and segments will be available for the resource in the `FROM` clause.
*   Selecting segments or metrics that are not compatible with each other.

#### FROM

The `FROM` clause specifies the main resource that will be returned. The resource in the `FROM` clause defines what fields can be used all of the other clauses for the given query. Only a single resource can be specified in the `FROM` clause. The `FROM` clause is **required** in a query。

While only one resource can exist in the `FROM` clause for a given query, fields from Attributed Resources may be available as well. These resources are implicitly joined with the resource in the `FROM` clause, so you only need to add their attributes to the `SELECT` clause to return their values. Not all resources have Attributed Resources. In the following example you can request both the ad group ID and the campaign ID from ad groups:

```
SELECT
    campaign.id,
    ad_group.id
FROM ad_group
```

The `resource_name` field of the main resource is always returned. In the following example, `ad_group.resource_name` will be included in the response despite not being explicitly selected in the query:

```
SELECT ad_group.id
FROM ad_group
```

The same is true for other resources when at least one field is selected. For example: `campaign.resource_name` will be included in the response for the following query:

```
SELECT
    campaign.id,
    ad_group.id
FROM ad_group
```

**Key Point:** If the resource in the `FROM` clause lists another resource as a `segment`, then selecting any attributes of that resource will act as a segment.

#### WHERE

The `WHERE` clause specifies conditions to apply when filtering data for the request. When using the `WHERE` clause, one or more conditions can be specified using `AND` to separate them. Each condition should follow the pattern `field_name Operator value`. The `WHERE` clause is **optional** in a query.

The following is an example of using `WHERE` to return metrics from a given time period:

```
SELECT
    campaign.id,
    campaign.name,
    metrics.impressions
FROM campaign
WHERE segments.date DURING LAST_30_DAYS
```

You can combine multiple conditions to filter the data. This example will request the number of clicks for all campaigns with impressions on mobile in the last 30 days.

```
SELECT
    campaign.id,
    campaign.name,
    segments.device,
    metrics.clicks
FROM campaign
WHERE metrics.impressions > 0
    AND segments.device = MOBILE
    AND segments.date DURING LAST_30_DAYS
```

Segments in the `WHERE` clause must be in the `SELECT` clause, with the following date segments, which are referred to as _core date segments_, being exceptions:

*   `segments.date`
*   `segments.week`
*   `segments.month`
*   `segments.quarter`
*   `segments.year`

In the following query, note that `segments.date` is selected. Because this segment is a core date segment, it requires a finite date range composed of _core date segments_ in the `WHERE` clause to be provided.

```
SELECT
    campaign.id,
    campaign.name,
    segments.date,
    metrics.clicks
FROM campaign
WHERE segments.date DURING LAST_30_DAYS
```

All segments that meet the above condition are: `segments.date`, `segments.week`, `segments.month`, `segments.quarter`, and `segments.year`. If any of these segments are selected, at least one of them must be used in the `WHERE` clause.

**Key Point:** The separator `AND` can only be used between operator conditions (`WHERE segments.device != "DESKTOP" AND segments.device != "MOBILE"`), and not within a single operator condition (`WHERE segments.device != "DESKTOP" AND "MOBILE"`),

When filtering, the case-sensitivity of your operator is important to keep in mind.

#### ORDER BY

The `ORDER BY` clause specifies the order in which the results are to be returned. This lets you arrange the data in ascending or descending order based on a field name. Each ordering is specified as a `field_name` followed by `ASC` or `DESC`. If neither `ASC` nor `DESC` is specified, the order defaults to `ASC`. The `ORDER BY` clause is **optional** in a query.

The following query orders the returned campaigns by the number of clicks from highest to lowest:

```
SELECT
    campaign.name,
    metrics.clicks
FROM campaign
ORDER BY metrics.clicks DESC
```

You can specify multiple fields in the `ORDER BY` clause using a comma-separated list. The ordering will occur in the same sequence as specified in the query. For example, in this query selecting ad group data, the results will be sorted in ascending order by campaign name, then in descending order by number of impressions, then in descending order by number of clicks:

```
SELECT
    campaign.name,
    ad_group.name,
    metrics.impressions,
    metrics.clicks
FROM ad_group
ORDER BY
    campaign.name,
    metrics.impressions DESC,
    metrics.clicks DESC
```

#### LIMIT

The `LIMIT` clause lets you specify the number of results to be returned. This is useful if you're only interested in a summary.

For example, `LIMIT` can be used to restrict the total number of results for the following query:

```
SELECT
    campaign.name,
    ad_group.name,
    segments.device,
    metrics.impressions
FROM ad_group
ORDER BY metrics.impressions DESC
LIMIT 50
```

**Key Point:** `LIMIT` lets you truncate the results.

#### PARAMETERS

The `PARAMETERS` clause lets you specify meta parameters for the request. These parameters may impact what kinds of rows are returned.

The following meta parameters are supported:

#### include\_drafts

Set `include_drafts` to `true` to allow draft entities to be returned. Defaults to `false`.

For example, the following query fetches draft campaigns along with regular campaigns:

```
SELECT campaign.name
FROM campaign
PARAMETERS include_drafts=true
```

### Additional language rules

In addition to the examples for each clause, Google Ads Query Language has the following behaviors that can be utilized:

*   It's **not** required for the main resource field to be in the `SELECT` clause for a query. For example, you might want to only use one or more main resource fields to filter data:

```
SELECT campaign.id
FROM ad_group
WHERE ad_group.status = PAUSED
```

*   Metrics can be exclusively selected for a given resource; no other fields from the resource are required in the query:

```
SELECT
    metrics.impressions,
    metrics.clicks,
    metrics.cost_micros
FROM campaign
```

*   Segmentation fields can be selected without any accompanying resource fields or metrics:

    SELECT segments.device FROM campaign

*   The `resource_name` field (`campaign.resource_name`, for example) can be used to filter or order data:

```
SELECT
    campaign.id,
    campaign.name
FROM campaign
WHERE campaign.resource_name = 'customers/1234567/campaigns/987654'
```