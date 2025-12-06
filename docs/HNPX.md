# HNPX Specification

A hierarchical XML format for planning and writing fiction. Enables structured decomposition from book-level overview to atomic paragraph units.

---

## Document Structure

A valid HNPX document is a single XML file with this strict hierarchy:

```
book → chapter → sequence → beat → paragraph
```

---

## Element Definitions

### `<book>`
The root element containing the entire work.

**Attributes:**
- `id` (required): Unique identifier, 6-character random string (lowercase letters + digits)

**Children:**
- `<summary>` (required)
- `<chapter>`

**Content:** None

**Example:**
```xml
<book id="a3f9b2">
  <summary>A young mage's journey to uncover her forgotten past.</summary>
</book>
```

---

### `<chapter>`
Major narrative division with a title.

**Attributes:**
- `id` (required): Unique identifier
- `title` (required): Chapter title
- `pov` (optional): Point-of-view character identifier

**Children:**
- `<summary>` (required)
- `<sequence>`

**Content:** None

**Example:**
```xml
<chapter id="k9p3q1" title="The Awakening" pov="mira">
  <summary>A young mage discovers her powers in the forbidden woods.</summary>
</chapter>
```

---

### `<sequence>`
Continuous narrative in a single location and time frame.

**Attributes:**
- `id` (required): Unique identifier
- `location` (optional): Location description
- `time` (optional): Time indicator (e.g., "night", "next day", "flashback")
- `pov` (optional): Overrides chapter POV if present

**Children:**
- `<summary>` (required)
- `<beat>`

**Content:** None

**Example:**
```xml
<sequence id="r4s8t6" location="Forest" time="night" pov="mira">
  <summary>Mira discovers an ancient shrine.</summary>
</sequence>
```

---

### `<beat>`
Narrative unit grouping related paragraphs within a sequence.

**Attributes:**
- `id` (required): Unique identifier

**Children:**
- `<summary>` (required)
- `<paragraph>`

**Content:** None

**Example:**
```xml
<beat id="u1v7w3">
  <summary>Entering the forbidden woods.</summary>
</beat>
```

---

### `<paragraph>`
Atomic narrative unit containing prose text.

**Attributes:**
- `id` (required): Unique identifier
- `mode` (optional): Narrative mode, one of:
  - `narration` (default)
  - `dialogue`
  - `internal`
- `char` (optional): Character identifier
  - Required when `mode="dialogue"`

**Children:**
- Text content (required)

**Content:** Plain text prose of the paragraph.

**Example:**
```xml
<paragraph id="z5y2x4" mode="narration">
  Mira pushed through the thick undergrowth, her breath fogging in the cold air.
</paragraph>
```

---

## ID Format

All `id` attributes must be:
- Unique within the document
- Exactly 6 characters
- Lowercase letters (a-z) and digits (0-9) only

Examples: `a3f9b2`, `c8e4d1`, `x7j5m2`

---

## Summary Requirement

Every container element (`book`, `chapter`, `sequence`, `beat`) must contain exactly one `<summary>` child element. `paragraph` can't have summary, only text content.

The `<summary>` element:
- Contains plain text
- May be multiple lines
- Describes the content/purpose of its parent
- Remains even when child elements are fully defined

---

## POV Inheritance

Point-of-view flows down the hierarchy:
1. Chapter `pov` sets default for all sequences
2. Sequence `pov` overrides chapter POV for that sequence

---

## Narrative Mode Rules

1. **`narration`** (default): Narrator's voice describing action, setting, or exposition.
2. **`dialogue`**: Character's spoken words. Must have `char` attribute.
3. **`internal`**: Character's thoughts.

Each paragraph should use one consistent mode.

---

## Validation Rules

A valid HNPX document must:
1. Have exactly one `<book>` root element
2. Contain only the elements defined in this specification
3. Have all required attributes present
4. Have unique `id` values throughout
5. Have `<summary>` child for every container node
6. Have `char` attribute when `mode="dialogue"`
7. Maintain the hierarchy: book → chapter → sequence → beat → paragraph

---

## Purpose

HNPX enables:
- Planning fiction at any level of detail
- Maintaining narrative structure
- Partial documentation (summaries without full text)
- Complete documentation (full prose ready for rendering)
- Tool-friendly processing with unique identifiers
- Consistent hierarchy for any narrative style
