// cytoscape-fcose ships no TypeScript types; it is a standard Cytoscape layout extension.
declare module "cytoscape-fcose" {
  import type { Ext } from "cytoscape";
  const ext: Ext;
  export default ext;
}
