# HNPX Specification

A hierarchical XML format for planning and writing fiction. Enables structured decomposition from book-level overview to atomic paragraph units.

---

## Document Structure

A valid HNPX document is a single XML file with this strict hierarchy:

```
book → chapter → sequence → beat → paragraph
```

Each element must have:
- A unique `id` attribute
- A `<summary>` child element
- No other child elements except those defined in this specification

---

## Element Definitions

### `<book>`
The root element containing the entire work.

**Attributes:**
- `id` (required): Unique identifier, 6-character random string (lowercase letters + digits)

**Children:**
- `<summary>` (required)
- `<chapter>` (zero or more)

**Content:** None

**Example:**
```xml
<book id="a3f9b2">
  <summary>A young mage's journey to uncover her forgotten past.</summary>
  <chapter id="k9p3q1" title="The Awakening">
    <!-- ... -->
  </chapter>
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
- `<sequence>` (zero or more)

**Content:** None

**Example:**
```xml
<chapter id="k9p3q1" title="The Awakening" pov="mira">
  <summary>A young mage discovers her powers in the forbidden woods.</summary>
  <sequence id="r4s8t6" loc="Forest">
    <!-- ... -->
  </sequence>
</chapter>
```

---

### `<sequence>`
Continuous narrative in a single location and time frame.

**Attributes:**
- `id` (required): Unique identifier
- `loc` (required): Location description
- `time` (optional): Time indicator (e.g., "night", "next day", "flashback")
- `pov` (optional): Overrides chapter POV if present

**Children:**
- `<summary>` (required)
- `<beat>` (zero or more)

**Content:** None

**Example:**
```xml
<sequence id="r4s8t6" loc="Forest" time="night" pov="mira">
  <summary>Mira discovers an ancient shrine.</summary>
  <beat id="u1v7w3">
    <!-- ... -->
  </beat>
</sequence>
```

---

### `<beat>`
Narrative unit grouping related paragraphs within a sequence.

**Attributes:**
- `id` (required): Unique identifier

**Children:**
- `<summary>` (required)
- `<paragraph>` (zero or more)

**Content:** None

**Example:**
```xml
<beat id="u1v7w3">
  <summary>Entering the forbidden woods.</summary>
  <paragraph id="z5y2x4" mode="narration">
    <!-- ... -->
  </paragraph>
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
  - Optional when `mode="internal"` (defaults to sequence/chapter POV)

**Children:**
- `<summary>` (required)
- Text content (optional)

**Content:** Plain text prose of the paragraph.

**Example:**
```xml
<paragraph id="z5y2x4" mode="narration">
  <summary>Mira pushes through the undergrowth.</summary>
  Mira pushed through the thick undergrowth, her breath fogging in the cold air.
</paragraph>

<paragraph id="l2k8j5" mode="dialogue" char="mira">
  <summary>Mira speaks her doubt.</summary>
</paragraph>
```

---

## ID Format

All `id` attributes must be:
- Unique within the document
- Exactly 6 characters
- Lowercase letters (a-z) and digits (0-9) only
- Generated randomly by tools (not sequential)

Examples: `a3f9b2`, `c8e4d1`, `x7j5m2`

---

## Summary Requirement

Every container element (`book`, `chapter`, `sequence`, `beat`, `paragraph`) must contain exactly one `<summary>` child element.

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
3. Paragraph `char` attribute identifies specific speaker/thinker

If a paragraph has `mode="internal"` but no `char` attribute, it defaults to the current POV (sequence or chapter).

---

## Narrative Mode Rules

1. **`narration`** (default): Narrator's voice describing action, setting, or exposition.
2. **`dialogue`**: Character's spoken words. Must have `char` attribute.
3. **`internal`**: Character's thoughts. `char` optional (defaults to current POV).

Each paragraph should use one consistent mode.

---

## Validation Rules

A valid HNPX document must:
1. Have exactly one `<book>` root element
2. Contain only the elements defined in this specification
3. Have all required attributes present
4. Have unique `id` values throughout
5. Have `<summary>` child for every container
6. Have `char` attribute when `mode="dialogue"`
7. Maintain the hierarchy: book → chapter → sequence → beat → paragraph

---

## Example Complete Document

```xml
<?xml version="1.0" encoding="UTF-8"?>
<book id="x7j5m2">
  <summary>A young mage's journey to uncover her forgotten past.</summary>
  
  <chapter id="k9p3q1" title="The Awakening" pov="mira">
    <summary>A young mage discovers her powers in the forbidden woods.</summary>
    
    <sequence id="r4s8t6" loc="Forest" time="night">
      <summary>Mira discovers an ancient shrine.</summary>
      
      <beat id="u1v7w3">
        <summary>Entering the forbidden woods.</summary>
        
        <paragraph id="z5y2x4" mode="narration">
          <summary>Mira pushes through the undergrowth.</summary>
          Mira pushed through the thick undergrowth, her breath fogging in the cold air.
        </paragraph>
        
        <paragraph id="m6n8b4" mode="narration">
          <summary>Description of the ancient trees.</summary>
          The ancient trees loomed overhead, their branches forming a canopy that blocked out the moon.
        </paragraph>
      </beat>
      
      <beat id="p9o3i7">
        <summary>Finding the shrine.</summary>
        
        <paragraph id="l2k8j5" mode="dialogue" char="mira">
          <summary>Mira speaks her doubt.</summary>
          "Is this... the place from my dreams?"
        </paragraph>
        
        <paragraph id="q1w9e3" mode="internal" char="mira">
          <summary>Mira's internal realization.</summary>
          This was exactly as she had dreamed it, down to the moss pattern on the stones.
        </paragraph>
      </beat>
    </sequence>
  </chapter>
</book>
```

---

## Purpose

HNPX enables:
- Planning fiction at any level of detail
- Maintaining narrative structure
- Partial documentation (summaries without full text)
- Complete documentation (full prose ready for rendering)
- Tool-friendly processing with unique identifiers
- Consistent hierarchy for any narrative style

All narrative content exists as plain text within `<paragraph>` elements. Rendering to final formatted prose is outside this specification's scope.