# pygdo-links
This module for the PyGDO chat framework collects links from any input line, stores title and description and makes these links searchable.

# Links (For Humans)

## Methods

- Links table: browse and search collected links, including their title,
  URL, host, description, sightings and votes. Soft-deleted links are excluded
  by default; staff can use `links --all` to include unapproved records.
- `$links.up <id>`: upvote a collected link. Its first upvote triggers
  a one-time announcement in channels that subscribe to link announcements.
  Announcements include the URL, its preview, vote count, and upvote command
  with ID.

## GDTs

- `links_collect`: opt in before collecting links from that
  channel. Collection and announcement subscriptions are separate settings.
- `links_abbo`: opt a channel in to receiving announcements.

## GDOs

- Links store their URL and available title and description. For plain-text
  files, the preview shows the first three lines together on one line.
- Exact repeated URLs increment a sighting count; a separate hostname enables
  searches by domain.
- HTML pages provide saved title and description previews as plain text.
- Staff can use `links.moderate <id>` to hide a link and `links.moderate <id>
  --approve=1` to restore it. Admins can permanently remove one with
  `links.delete <id> --confirm=1`.
- `link_spreaded` records whether a spread attempt has been claimed.

# Links (For ALs)

Implementation is local and has focused unit tests, but schema migration,
multi-process concurrency and end-to-end connector delivery remain untested.
Do not enable collection in production until these have been tested. A Dog
timer claims a voted link before its one best-effort broadcast attempt; a crash
after the claim can prevent delivery, and no failed destination is retried.

## Methods

- Links table: provide a searchable table of visible `GDO_Link` records
  with their metadata, sighting counts and vote results.
- Collection: extract links only from opted-in channels; preserve the
  existing searchable link records. Do not collect private messages by default.
  On first discovery, notify only the originating channel with title,
  description and `links.up <id>` using that channel's command trigger.
- `links.up`: use the reusable `vote` module to record votes and trigger
  the first spread once. Include the vote count, destination connector's command
  trigger and link ID in the announcement. Make one best-effort broadcast attempt;
  do not retry channels that are offline or fail during that attempt.
- Text preview: fetch at most a bounded amount, render the first three
  lines as a single line, and handle unavailable or non-text content gracefully.
  Restrict fetching and redirects to safe public HTTP(S) destinations; use
  timeouts and size limits to prevent internal-network access and resource abuse.
- HTML preview: extract and save bounded title and meta description as
  plain text; never execute remote markup.
- Deletion: soft-deleted records are excluded from public search and spreading;
  authorized hard deletion permanently removes the selected link and related
  data according to the applicable retention policy.

## GDTs

- `links_collect` is the opt-in channel setting for collection.
- `links_abbo` is an independent opt-in channel setting for announcements.
- `link_spreaded` is a Boolean on the link record.
- Reuse `gdo.net.GDT_Host` for the host field. It currently allows
  ASCII strings up to 96 characters and does not validate host syntax unless
  resolution is requested; decide how to handle longer or international hosts
  without relying on DNS resolution as a safety check.

## GDOs

- `GDO_Link` retains the URL, metadata, creator and timestamp, spread state,
  and a link-specific vote table using the `vote` module.
- The module declares `vote` as a dependency.
- Store host, path and query separately while preserving the original URL; use a
  normalized hostname for indexing. Query strings may contain sensitive data
  and require a privacy and redistribution policy. Track link sightings and
  duplicate occurrences only in opted-in channels (TODO).

## Ideas and open questions

- Decide whether each user can upvote a link only once, how sightings are
  counted, and which URL differences are considered duplicates across channels.
- Decide whether hostname-level indexing is sufficient or a separate domain
  entity is useful; a hostname is not always the registrable domain.
- A global spread flag records the one broadcast attempt, not confirmed delivery
  to every channel. Channels subscribing later do not receive a replay.
- Decide whether a collected channel link may be redistributed to other opted-in
  channels, and how to handle links containing private tokens or query strings.
