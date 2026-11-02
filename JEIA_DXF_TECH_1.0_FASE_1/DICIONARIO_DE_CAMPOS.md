# Dicionário completo de campos — JEIA_DXF_TECH 1.0

Gerado a partir do schema entregue. O schema define limites e cardinalidades; as regras normativas definem relações entre os campos. Obrigatório exige presença; `null` só é permitido onde listado. Arrays obrigatórios podem ser vazios salvo minItems. Tipos fechados rejeitam propriedades desconhecidas. Mapas brutos explicitamente abertos preservam atributos e não autorizam consumo automático.

## Pacote raiz

Especificacao documental. Nao implementa extracao, reconhecimento nem autorizacao CNC. Regras semanticas complementares em REGRAS_E_INVARIANTES.md.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `contract` | Obrigatório | 'JEIA_DXF_TECH' | Definido pelas regras normativas e pelo nome do campo. |
| `version` | Obrigatório | '1.0' | Definido pelas regras normativas e pelo nome do campo. |
| `context` | Obrigatório | Context | Definido pelas regras normativas e pelo nome do campo. |
| `document` | Obrigatório | Document | Definido pelas regras normativas e pelo nome do campo. |
| `sources` | Obrigatório | array<Source> | Definido pelas regras normativas e pelo nome do campo. |
| `frames` | Obrigatório | array<Frame> | Definido pelas regras normativas e pelo nome do campo. |
| `transforms` | Obrigatório | array<Transform> | Definido pelas regras normativas e pelo nome do campo. |
| `spaces` | Obrigatório | array<Space> | Definido pelas regras normativas e pelo nome do campo. |
| `viewports` | Obrigatório | array<Viewport> | Definido pelas regras normativas e pelo nome do campo. |
| `layers` | Obrigatório | array<Layer> | Definido pelas regras normativas e pelo nome do campo. |
| `blockDefinitions` | Obrigatório | array<BlockDefinition> | Definido pelas regras normativas e pelo nome do campo. |
| `blockInstances` | Obrigatório | array<BlockInstance> | Definido pelas regras normativas e pelo nome do campo. |
| `entities` | Obrigatório | array<Entity> | Definido pelas regras normativas e pelo nome do campo. |
| `occurrences` | Obrigatório | array<Occurrence> | Definido pelas regras normativas e pelo nome do campo. |
| `geometries` | Obrigatório | array<Geometry> | Definido pelas regras normativas e pelo nome do campo. |
| `dimensionStyles` | Obrigatório | array<DimensionStyle> | Definido pelas regras normativas e pelo nome do campo. |
| `dimensions` | Obrigatório | array<Dimension> | Definido pelas regras normativas e pelo nome do campo. |
| `tolerances` | Obrigatório | array<Tolerance> | Definido pelas regras normativas e pelo nome do campo. |
| `annotations` | Obrigatório | array<Annotation> | Definido pelas regras normativas e pelo nome do campo. |
| `parts` | Obrigatório | array<Part> | Definido pelas regras normativas e pelo nome do campo. |
| `views` | Obrigatório | array<View> | Definido pelas regras normativas e pelo nome do campo. |
| `evidence` | Obrigatório | array<Evidence> | Definido pelas regras normativas e pelo nome do campo. |
| `classifications` | Obrigatório | array<Classification> | Definido pelas regras normativas e pelo nome do campo. |
| `observations` | Obrigatório | array<Observation> | Definido pelas regras normativas e pelo nome do campo. |
| `featureRelations` | Obrigatório | array<FeatureRelation> | Definido pelas regras normativas e pelo nome do campo. |
| `features` | Obrigatório | array<Feature> | Definido pelas regras normativas e pelo nome do campo. |
| `setups` | Obrigatório | array<Setup> | Definido pelas regras normativas e pelo nome do campo. |
| `operations` | Obrigatório | array<Operation> | Definido pelas regras normativas e pelo nome do campo. |
| `numericProfiles` | Obrigatório | array<NumericProfile> | Definido pelas regras normativas e pelo nome do campo. |
| `reconciliations` | Obrigatório | array<Reconciliation> | Definido pelas regras normativas e pelo nome do campo. |
| `decisions` | Obrigatório | array<Decision> | Definido pelas regras normativas e pelo nome do campo. |
| `diagnostics` | Obrigatório | array<Diagnostic> | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | PackageValidation | Definido pelas regras normativas e pelo nome do campo. |
## Id

Identificador opaco, estavel no mesmo documento e revisao; unicidade global no pacote (ID-01).

string

## Sha256

Consulte as regras normativas para significado e dependências.

string

## JsonValue

Consulte as regras normativas para significado e dependências.

['string', 'number', 'boolean', 'null'] ou array<JsonValue> ou object

## Vec3

Consulte as regras normativas para significado e dependências.

array<number>

## Matrix4

Consulte as regras normativas para significado e dependências.

array<array<number>>

## State

Consulte as regras normativas para significado e dependências.

enum: unknown, extracted, interpreted, verified, confirmed, conflicting, rejected, unsupported, not_applicable

## Target

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `kind` | Obrigatório | enum: document, source, space, frame, transform, layer, block_definition, block_instance, entity, occurrence, geometry, dimension_style, dimension, tolerance, annotation, view, part, observation, feature, feature_relation, setup, operation, classification, reconciliation, decision, evidence, diagnostic, numeric_profile | Definido pelas regras normativas e pelo nome do campo. |
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
## Validation

Estado de conhecimento; nao representa autorizacao de fabricacao. Estados possuem invariantes ST-01 a ST-05.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `state` | Obrigatório | State | Definido pelas regras normativas e pelo nome do campo. |
| `evidenceIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `diagnosticIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `reason` | Obrigatório | string ou null | Definido pelas regras normativas e pelo nome do campo. |
## Quantity

Escalar, com unidade e origem por evidencias. unknown/unsupported exigem value=null; zero valido nao significa ausencia.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `value` | Obrigatório | number ou null | Definido pelas regras normativas e pelo nome do campo. |
| `unit` | Obrigatório | enum: mm, rad, deg, drawing_unit, paper_unit, mm2, mm3, dimensionless, unknown | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
## QuantityMap

Grandezas nomeadas. Vocabulário e unidades em QT-01; chaves desconhecidas nao podem alimentar calculos automaticamente.

object

## Scale

Razao adimensional comprimento representado / comprimento fisico. Nao e escala de impressao nem INSERT.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `drawingPerPart` | Obrigatório | number ou null | Definido pelas regras normativas e pelo nome do campo. |
| `method` | Obrigatório | enum: model_1_to_1_verified, explicit_annotation, dimension_geometry_comparison, operator, unknown | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
## Units

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `rawInsunits` | Obrigatório | integer | Definido pelas regras normativas e pelo nome do campo. |
| `rawMeasurement` | Obrigatório | integer ou null | Definido pelas regras normativas e pelo nome do campo. |
| `resolvedUnit` | Obrigatório | string ou null | Definido pelas regras normativas e pelo nome do campo. |
| `mmPerDrawingUnit` | Obrigatório | number ou null | Definido pelas regras normativas e pelo nome do campo. |
| `resolutionMethod` | Obrigatório | enum: header, operator, documented_conversion, unknown | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
## Context

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `requestId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `selectionGeneration` | Obrigatório | integer | Definido pelas regras normativas e pelo nome do campo. |
| `analysisRevision` | Obrigatório | integer | Definido pelas regras normativas e pelo nome do campo. |
| `purpose` | Obrigatório | enum: production_analysis, synthetic_example | Definido pelas regras normativas e pelo nome do campo. |
| `producer` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `createdAt` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
## Document

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `fileName` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `sha256` | Obrigatório | Sha256 | Definido pelas regras normativas e pelo nome do campo. |
| `byteLength` | Obrigatório | integer | Definido pelas regras normativas e pelo nome do campo. |
| `dxfVersion` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `encoding` | Obrigatório | string ou null | Definido pelas regras normativas e pelo nome do campo. |
| `units` | Obrigatório | Units | Definido pelas regras normativas e pelo nome do campo. |
| `rawHeader` | Obrigatório | object | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
## Source

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `kind` | Obrigatório | enum: dxf_original, ezdxf, freecad, operator, rule_engine | Definido pelas regras normativas e pelo nome do campo. |
| `version` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `inputSha256` | Obrigatório | Sha256 | Definido pelas regras normativas e pelo nome do campo. |
| `options` | Obrigatório | object | Definido pelas regras normativas e pelo nome do campo. |
| `capabilities` | Obrigatório | array<string> | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
## Frame

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `kind` | Obrigatório | enum: entity_ocs, block_definition, document_wcs, paper, view, part, setup | Definido pelas regras normativas e pelo nome do campo. |
| `unit` | Obrigatório | enum: drawing_unit, mm, paper_unit, dimensionless | Definido pelas regras normativas e pelo nome do campo. |
| `spaceId` | Obrigatório | Id ou null | Definido pelas regras normativas e pelo nome do campo. |
| `description` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
## Transform

Matriz afim 4x4 row-major, vetores-coluna: p_dest=M*p_origem. Sem transformacao numerica confiavel, matrix=null.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `fromFrameId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `toFrameId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `matrix` | Obrigatório | Matrix4 ou null | Definido pelas regras normativas e pelo nome do campo. |
| `kind` | Obrigatório | enum: ocs_to_wcs, block_instance, occurrence_to_space, unit_conversion, orthographic_viewport, view_to_part, part_to_setup, space_to_view | Definido pelas regras normativas e pelo nome do campo. |
| `componentTransformIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
## Viewport

Viewport referencia geometria Model, nao cria nova peca nem duplica suas entidades. Perspectiva nao autoriza medicao inversa por fator escalar.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `entityId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `modelSpaceId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `paperFrameId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `viewCenter` | Obrigatório | Vec3 | Definido pelas regras normativas e pelo nome do campo. |
| `viewTarget` | Obrigatório | Vec3 | Definido pelas regras normativas e pelo nome do campo. |
| `viewDirection` | Obrigatório | Vec3 | Definido pelas regras normativas e pelo nome do campo. |
| `twistRad` | Obrigatório | number | Definido pelas regras normativas e pelo nome do campo. |
| `paperCenter` | Obrigatório | Vec3 | Definido pelas regras normativas e pelo nome do campo. |
| `paperHeight` | Obrigatório | Quantity | Definido pelas regras normativas e pelo nome do campo. |
| `modelViewHeight` | Obrigatório | Quantity | Definido pelas regras normativas e pelo nome do campo. |
| `projection` | Obrigatório | enum: orthographic, perspective, unknown | Definido pelas regras normativas e pelo nome do campo. |
| `modelToPaperTransformId` | Obrigatório | Id ou null | Definido pelas regras normativas e pelo nome do campo. |
| `projectionMatrix` | Obrigatório | Matrix4 ou null | Definido pelas regras normativas e pelo nome do campo. |
| `clipBoundaryOccurrenceIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
## Space

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `kind` | Obrigatório | enum: model, paper | Definido pelas regras normativas e pelo nome do campo. |
| `name` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `frameId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `paperUnit` | Obrigatório | enum: mm, inch, unknown, not_applicable | Definido pelas regras normativas e pelo nome do campo. |
| `viewportIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
## Layer

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `name` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `color` | Obrigatório | JsonValue ou null | Definido pelas regras normativas e pelo nome do campo. |
| `linetype` | Obrigatório | string ou null | Definido pelas regras normativas e pelo nome do campo. |
| `lineweight` | Obrigatório | number ou null | Definido pelas regras normativas e pelo nome do campo. |
| `visible` | Obrigatório | boolean ou null | Definido pelas regras normativas e pelo nome do campo. |
| `frozen` | Obrigatório | boolean ou null | Definido pelas regras normativas e pelo nome do campo. |
| `locked` | Obrigatório | boolean ou null | Definido pelas regras normativas e pelo nome do campo. |
| `plotEnabled` | Obrigatório | boolean ou null | Definido pelas regras normativas e pelo nome do campo. |
| `rawAttributes` | Obrigatório | object | Definido pelas regras normativas e pelo nome do campo. |
## BlockDefinition

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `name` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `basePoint` | Obrigatório | Vec3 | Definido pelas regras normativas e pelo nome do campo. |
| `frameId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `declaredInsunits` | Obrigatório | integer ou null | Definido pelas regras normativas e pelo nome do campo. |
| `entityIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `externalReference` | Obrigatório | string ou null | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
## BlockInstance

Uma instancia por celula de MINSERT. transformId mapeia frame da definicao para frame do pai; formulas BL-01/02.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `insertEntityId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `definitionId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `parentInstanceId` | Obrigatório | Id ou null | Definido pelas regras normativas e pelo nome do campo. |
| `spaceId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `row` | Obrigatório | integer | Definido pelas regras normativas e pelo nome do campo. |
| `column` | Obrigatório | integer | Definido pelas regras normativas e pelo nome do campo. |
| `insertPoint` | Obrigatório | Vec3 | Ponto bruto do INSERT/array antes do deslocamento da célula (BL-02). |
| `scale` | Obrigatório | Vec3 | Definido pelas regras normativas e pelo nome do campo. |
| `rotationRad` | Obrigatório | number | Definido pelas regras normativas e pelo nome do campo. |
| `extrusion` | Obrigatório | Vec3 | Definido pelas regras normativas e pelo nome do campo. |
| `rowSpacing` | Obrigatório | number | Definido pelas regras normativas e pelo nome do campo. |
| `columnSpacing` | Obrigatório | number | Definido pelas regras normativas e pelo nome do campo. |
| `transformId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
## RawGroup

Preservar repeticoes e ordem. rawValue pode ser vazio; grupos desconhecidos sao mantidos.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `code` | Obrigatório | integer | Definido pelas regras normativas e pelo nome do campo. |
| `rawValue` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `decodedValue` | Obrigatório | JsonValue | Definido pelas regras normativas e pelo nome do campo. |
## Origin

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `sourceId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `handle` | Obrigatório | string ou null | Definido pelas regras normativas e pelo nome do campo. |
| `ownerHandle` | Obrigatório | string ou null | Definido pelas regras normativas e pelo nome do campo. |
| `ordinal` | Obrigatório | integer | Definido pelas regras normativas e pelo nome do campo. |
| `identityMethod` | Obrigatório | enum: dxf_handle, owner_and_ordinal | Definido pelas regras normativas e pelo nome do campo. |
## Entity

rawRecordDigest opcional auxilia comparacao; nunca substitui handle/caminho por identidade geometrica.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `dxfType` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `origin` | Obrigatório | Origin | Definido pelas regras normativas e pelo nome do campo. |
| `owner` | Obrigatório | object | Definido pelas regras normativas e pelo nome do campo. |
| `layerId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `linetype` | Obrigatório | string ou null | Definido pelas regras normativas e pelo nome do campo. |
| `rawFrameId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `geometryIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `rawGroups` | Obrigatório | array<RawGroup> | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
| `rawRecordDigest` | Opcional | Sha256 | Definido pelas regras normativas e pelo nome do campo. |
## Occurrence

Uma ocorrencia por entidade posicionada; contexto de instancia preservado inclusive quando geometria coincide.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `entityId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `spaceId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `instancePath` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `effectiveLayerId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `effectiveLinetype` | Obrigatório | string ou null | Definido pelas regras normativas e pelo nome do campo. |
| `effectiveVisible` | Obrigatório | boolean ou null | Definido pelas regras normativas e pelo nome do campo. |
| `canonicalGeometryId` | Obrigatório | Id ou null | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
| `transformToSpaceId` | Obrigatório | Id | Mapeamento da entidade para o frame do proprio espaco: WCS do Model ou coordenadas de referencia do layout, nunca Paper -> Model implicitamente. |
## GeometryPayload

Consulte as regras normativas para significado e dependências.

**POINT** — `type`: 'POINT', `point`: Vec3. Todos os campos da variante são obrigatórios.

**LINE** — `type`: 'LINE', `start`: Vec3, `end`: Vec3. Todos os campos da variante são obrigatórios.

**CIRCLE** — `type`: 'CIRCLE', `center`: Vec3, `normal`: Vec3, `radius`: number. Todos os campos da variante são obrigatórios.

**ARC** — `type`: 'ARC', `center`: Vec3, `normal`: Vec3, `xAxis`: Vec3, `radius`: number, `startRad`: number, `sweepRad`: number. Todos os campos da variante são obrigatórios.

**ELLIPSE** — `type`: 'ELLIPSE', `center`: Vec3, `majorAxis`: Vec3, `minorAxis`: Vec3, `startRad`: number, `sweepRad`: number. Todos os campos da variante são obrigatórios.

**POLYLINE** — `type`: 'POLYLINE', `vertices`: array<object>, `closed`: boolean, `normal`: Vec3, `elevation`: number, `is3d`: boolean. Todos os campos da variante são obrigatórios.

**BSPLINE** — `type`: 'BSPLINE', `degree`: integer, `controlPoints`: array<Vec3>, `knots`: array<number>, `multiplicities`: array<integer>, `weights`: array<number> ou null, `periodic`: boolean, `closed`: boolean. Todos os campos da variante são obrigatórios.

**BREP_SUMMARY** — `type`: 'BREP_SUMMARY', `solids`: integer, `faces`: integer, `edges`: integer, `valid`: boolean, `bboxMin`: Vec3 ou null, `bboxMax`: Vec3 ou null, `volume`: Quantity ou null. Todos os campos da variante são obrigatórios.

**UNSUPPORTED** — `type`: 'UNSUPPORTED', `originalType`: string, `reason`: string. Todos os campos da variante são obrigatórios.

**COMPOSITE_CURVE** — `type`: 'COMPOSITE_CURVE', `segments`: array<object>, `closed`: boolean. Todos os campos da variante são obrigatórios.

## Geometry

Observacoes dos motores ficam separadas. Geometria FreeCAD sem identidade fica sem entityId/occurrenceId e com sourceObjectKey; nao fabricar vinculo.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `sourceId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `entityId` | Obrigatório | Id ou null | Definido pelas regras normativas e pelo nome do campo. |
| `occurrenceId` | Obrigatório | Id ou null | Definido pelas regras normativas e pelo nome do campo. |
| `sourceObjectKey` | Obrigatório | string ou null | Definido pelas regras normativas e pelo nome do campo. |
| `frameId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `payload` | Obrigatório | GeometryPayload | Definido pelas regras normativas e pelo nome do campo. |
| `approximation` | Obrigatório | enum: analytic, summary, unsupported, approximate | Definido pelas regras normativas e pelo nome do campo. |
| `derivedFromGeometryIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
| `appliedTransformIds` | Obrigatório | array<Id> | Transforms aplicados, do primeiro ao ultimo, entre os frames da geometria de origem e desta geometria; ordem normativa TR-01. |
| `approximationError` | Opcional | Quantity ou null | Opcional para representacao exata; para approximate, campo obrigatorio (null indica erro nao quantificado e bloqueia uso dimensional). |
## DimensionStyle

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `name` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `rawAttributes` | Obrigatório | object | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
## Dimension

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `entityId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `occurrenceId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `kind` | Obrigatório | enum: linear, aligned, angular, diameter, radius, ordinate, arc_length, unknown | Definido pelas regras normativas e pelo nome do campo. |
| `styleId` | Obrigatório | Id ou null | Definido pelas regras normativas e pelo nome do campo. |
| `rawMeasurement` | Obrigatório | Quantity | Definido pelas regras normativas e pelo nome do campo. |
| `computedMeasurement` | Obrigatório | Quantity | Definido pelas regras normativas e pelo nome do campo. |
| `displayMeasurement` | Obrigatório | Quantity | Definido pelas regras normativas e pelo nome do campo. |
| `rawText` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `displayText` | Obrigatório | string ou null | Definido pelas regras normativas e pelo nome do campo. |
| `rawOverrides` | Obrigatório | object | Definido pelas regras normativas e pelo nome do campo. |
| `resolvedStyle` | Obrigatório | object | Definido pelas regras normativas e pelo nome do campo. |
| `definitionPoints` | Obrigatório | array<Vec3> | Definido pelas regras normativas e pelo nome do campo. |
| `pointFrameId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `associatedOccurrenceIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `toleranceIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
## Tolerance

Nao inventar tolerancia ausente. Nao confundir tolerancia numerica do software com requisito de fabricacao.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `targetDimensionIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `targetFeatureIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `kind` | Obrigatório | enum: bilateral, unilateral, limits, geometric, general_note, unknown | Definido pelas regras normativas e pelo nome do campo. |
| `interpretation` | Obrigatório | enum: signed_deviation, absolute_limits, geometric_zone, unparsed | Definido pelas regras normativas e pelo nome do campo. |
| `lower` | Obrigatório | Quantity ou null | Definido pelas regras normativas e pelo nome do campo. |
| `upper` | Obrigatório | Quantity ou null | Definido pelas regras normativas e pelo nome do campo. |
| `rawText` | Obrigatório | string ou null | Definido pelas regras normativas e pelo nome do campo. |
| `standardReference` | Obrigatório | string ou null | Definido pelas regras normativas e pelo nome do campo. |
| `datumAnnotationIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
## Annotation

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `entityId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `occurrenceId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `kind` | Obrigatório | enum: text, mtext, attribute, attribute_definition, leader, surface_finish, datum, gdt, hatch, unknown | Definido pelas regras normativas e pelo nome do campo. |
| `rawText` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `plainText` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `anchor` | Obrigatório | Vec3 ou null | Definido pelas regras normativas e pelo nome do campo. |
| `frameId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `associatedOccurrenceIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `interpretation` | Obrigatório | JsonValue ou null | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
## View

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `spaceId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `frameId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `partId` | Obrigatório | Id ou null | Definido pelas regras normativas e pelo nome do campo. |
| `occurrenceIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `viewportId` | Obrigatório | Id ou null | Definido pelas regras normativas e pelo nome do campo. |
| `role` | Obrigatório | enum: front, top, side, section, detail, auxiliary, unknown | Definido pelas regras normativas e pelo nome do campo. |
| `scale` | Obrigatório | Scale | Definido pelas regras normativas e pelo nome do campo. |
| `viewToPartTransformId` | Obrigatório | Id ou null | Definido pelas regras normativas e pelo nome do campo. |
| `enabledForPlanning` | Obrigatório | boolean | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
| `spaceToViewTransformId` | Obrigatório | Id ou null | Mapeia coordenadas do espaco de origem para coordenadas locais representadas da vista; nao inclui escala fisica drawingPerPart. |
## Part

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `label` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `viewIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `featureIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `referenceViewId` | Obrigatório | Id ou null | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
## Evidence

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `sourceId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `targets` | Obrigatório | array<Target> | Definido pelas regras normativas e pelo nome do campo. |
| `family` | Obrigatório | enum: topology, dxf_structure, text_semantics, dimensional, projection_consistency, template_verified, layer_hint, position_hint, operator | Definido pelas regras normativas e pelo nome do campo. |
| `independenceKey` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `method` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `description` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `value` | Obrigatório | JsonValue | Definido pelas regras normativas e pelo nome do campo. |
| `reliability` | Obrigatório | enum: observed, heuristic, confirmed | Definido pelas regras normativas e pelo nome do campo. |
## CandidateClass

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `class` | Obrigatório | enum: piece_geometry, sheet_frame, title_block, dimension_annotation, technical_annotation, centerline, hidden_geometry, hatch, construction, unknown | Definido pelas regras normativas e pelo nome do campo. |
| `evidenceIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `score` | Obrigatório | number ou null | Definido pelas regras normativas e pelo nome do campo. |
## Classification

Score nao e probabilidade calibrada. Exclusao automatica exige evidencias independentes substantivas (CL-02).

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `targets` | Obrigatório | array<Target> | Definido pelas regras normativas e pelo nome do campo. |
| `candidates` | Obrigatório | array<CandidateClass> | Definido pelas regras normativas e pelo nome do campo. |
| `selectedClass` | Obrigatório | enum: piece_geometry, sheet_frame, title_block, dimension_annotation, technical_annotation, centerline, hidden_geometry, hatch, construction, unknown ou null | Definido pelas regras normativas e pelo nome do campo. |
| `inclusion` | Obrigatório | enum: included, excluded, pending | Definido pelas regras normativas e pelo nome do campo. |
| `decisionId` | Obrigatório | Id ou null | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
## Observation

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `partId` | Obrigatório | Id ou null | Definido pelas regras normativas e pelo nome do campo. |
| `viewId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `occurrenceIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `kind` | Obrigatório | enum: hole_candidate, slot_candidate, pocket_candidate, outer_profile, axis_candidate, shoulder_candidate, unknown | Definido pelas regras normativas e pelo nome do campo. |
| `quantities` | Obrigatório | QuantityMap | Definido pelas regras normativas e pelo nome do campo. |
| `axisFrameId` | Obrigatório | Id ou null | Definido pelas regras normativas e pelo nome do campo. |
| `accessOccurrenceIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
## FeatureRelation

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `leftObservationId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `rightObservationId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `relation` | Obrigatório | enum: same_feature, different_feature, possible_same_feature | Definido pelas regras normativas e pelo nome do campo. |
| `decisionId` | Obrigatório | Id ou null | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
## Feature

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `partId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `kind` | Obrigatório | enum: hole, slot, pocket, outer_profile, axis, shoulder, unknown | Definido pelas regras normativas e pelo nome do campo. |
| `observationIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `identityState` | Obrigatório | enum: tentative, distinct, confirmed, ambiguous | Definido pelas regras normativas e pelo nome do campo. |
| `quantities` | Obrigatório | QuantityMap | Definido pelas regras normativas e pelo nome do campo. |
| `axisFrameId` | Obrigatório | Id ou null | Definido pelas regras normativas e pelo nome do campo. |
| `throughState` | Obrigatório | enum: through, blind, unknown, not_applicable | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
## Setup

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `partId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `frameId` | Obrigatório | Id ou null | Definido pelas regras normativas e pelo nome do campo. |
| `accessOccurrenceIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
## Operation

Intencao de planejamento, nao codigo executavel. Chave semantica OP-01 impede duplicacao mesmo com IDs distintos.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `partId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `featureIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `stage` | Obrigatório | enum: marking, preparation, drilling, boring, reaming, threading, roughing, finishing, deburring, inspection, other | Definido pelas regras normativas e pelo nome do campo. |
| `processVariant` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `passGroup` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `setupId` | Obrigatório | Id ou null | Definido pelas regras normativas e pelo nome do campo. |
| `status` | Obrigatório | enum: proposed, confirmed, blocked, rejected | Definido pelas regras normativas e pelo nome do campo. |
| `quantity` | Obrigatório | integer | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
## NumericProfile

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `lengthAbsMm` | Obrigatório | number | Definido pelas regras normativas e pelo nome do campo. |
| `lengthRel` | Obrigatório | number | Definido pelas regras normativas e pelo nome do campo. |
| `angleAbsRad` | Obrigatório | number | Definido pelas regras normativas e pelo nome do campo. |
| `volumeAbsMm3` | Obrigatório | number | Definido pelas regras normativas e pelo nome do campo. |
| `volumeRel` | Obrigatório | number | Definido pelas regras normativas e pelo nome do campo. |
| `purpose` | Obrigatório | 'software_comparison_only' | Definido pelas regras normativas e pelo nome do campo. |
| `description` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
## SourceObservation

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `sourceId` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `geometryId` | Obrigatório | Id ou null | Definido pelas regras normativas e pelo nome do campo. |
| `quantity` | Obrigatório | Quantity ou null | Definido pelas regras normativas e pelo nome do campo. |
| `sourceObjectKey` | Obrigatório | string ou null | Definido pelas regras normativas e pelo nome do campo. |
## Reconciliation

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `subject` | Obrigatório | Target | Definido pelas regras normativas e pelo nome do campo. |
| `property` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `observations` | Obrigatório | array<SourceObservation> | Definido pelas regras normativas e pelo nome do campo. |
| `outcome` | Obrigatório | enum: agree, differ, missing, ambiguous, not_comparable | Definido pelas regras normativas e pelo nome do campo. |
| `numericProfileId` | Obrigatório | Id ou null | Definido pelas regras normativas e pelo nome do campo. |
| `maxAbsoluteDelta` | Obrigatório | number ou null | Definido pelas regras normativas e pelo nome do campo. |
| `deltaUnit` | Obrigatório | enum: mm, rad, mm3, dimensionless, not_applicable | Definido pelas regras normativas e pelo nome do campo. |
| `selectedObservationId` | Obrigatório | Id ou null | Definido pelas regras normativas e pelo nome do campo. |
| `decisionId` | Obrigatório | Id ou null | Definido pelas regras normativas e pelo nome do campo. |
| `validation` | Obrigatório | Validation | Definido pelas regras normativas e pelo nome do campo. |
## Decision

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `actor` | Obrigatório | object | Definido pelas regras normativas e pelo nome do campo. |
| `time` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `action` | Obrigatório | enum: confirm, reject, resolve_conflict, set_units, set_scale, associate_views, associate_features, classify | Definido pelas regras normativas e pelo nome do campo. |
| `targets` | Obrigatório | array<Target> | Definido pelas regras normativas e pelo nome do campo. |
| `evidenceIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `reason` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `binding` | Obrigatório | object | Definido pelas regras normativas e pelo nome do campo. |
| `supersedesDecisionId` | Obrigatório | Id ou null | Definido pelas regras normativas e pelo nome do campo. |
## Diagnostic

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `id` | Obrigatório | Id | Definido pelas regras normativas e pelo nome do campo. |
| `code` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `severity` | Obrigatório | enum: info, warning, error, blocker | Definido pelas regras normativas e pelo nome do campo. |
| `targets` | Obrigatório | array<Target> | Definido pelas regras normativas e pelo nome do campo. |
| `message` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
| `details` | Obrigatório | JsonValue | Definido pelas regras normativas e pelo nome do campo. |
| `blocksConsumers` | Obrigatório | array<enum: visualization, material, process, cost> | Definido pelas regras normativas e pelo nome do campo. |
| `status` | Obrigatório | enum: open, resolved, accepted_limitation | Definido pelas regras normativas e pelo nome do campo. |
| `evidenceIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
## Eligibility

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `scope` | Obrigatório | Target | Definido pelas regras normativas e pelo nome do campo. |
| `consumer` | Obrigatório | enum: visualization, material, process, cost | Definido pelas regras normativas e pelo nome do campo. |
| `status` | Obrigatório | enum: eligible, provisional, blocked, not_assessed | Definido pelas regras normativas e pelo nome do campo. |
| `blockingDiagnosticIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `requiredDecisionIds` | Obrigatório | array<Id> | Definido pelas regras normativas e pelo nome do campo. |
| `reason` | Obrigatório | string | Definido pelas regras normativas e pelo nome do campo. |
## PackageValidation

Consulte as regras normativas para significado e dependências.

| Campo | Presença | Tipo | Observação |
|---|---|---|---|
| `stage` | Obrigatório | enum: draft, extracted, reconciled, reviewed | Definido pelas regras normativas e pelo nome do campo. |
| `schemaStatus` | Obrigatório | enum: not_checked, valid, invalid | Definido pelas regras normativas e pelo nome do campo. |
| `semanticStatus` | Obrigatório | enum: not_checked, valid, invalid | Definido pelas regras normativas e pelo nome do campo. |
| `eligibility` | Obrigatório | array<Eligibility> | Definido pelas regras normativas e pelo nome do campo. |
| `cncReleased` | Obrigatório | False | Definido pelas regras normativas e pelo nome do campo. |
