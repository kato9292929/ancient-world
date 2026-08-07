// aw-data の公開エントリ。他パッケージはここから型とデータを読む。
export type {
  Site,
  AwEvent,
  Cluster,
  CoordStatus,
  CoordSource,
  EraStatus,
  FloodLayerAttributes,
} from "./types.js";

export type { CoordCandidate, CoordResolution } from "./coords.js";
export {
  parseWikidataResponse,
  parsePleiadesResponse,
  resolveCoord,
  parsePointWkt,
  qCodeFromUri,
} from "./coords.js";

import sitesJson from "../data/sites.json" with { type: "json" };
import eventsJson from "../data/events.json" with { type: "json" };
import clustersJson from "../data/clusters.json" with { type: "json" };
import type { Site, AwEvent, Cluster } from "./types.js";

export const sites = sitesJson as Site[];
export const events = eventsJson as AwEvent[];
export const clusters = clustersJson as Cluster[];
