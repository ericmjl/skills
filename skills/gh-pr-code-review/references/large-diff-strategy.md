# Large-diff strategy

Use when `gh pr diff` is too large to review whole: many files, a long
unified diff, or the packed text would crowd out the rest of the review.
Always tell the user which files and hunks you omitted.

Skip binaries and non-code (images, PDFs). Prefer the repo's main
languages. `gh api repos/{owner}/{repo}/languages` is a cheap hint; file
extensions in the PR also work.

## Pack the diff

1. **Language, then size.** Group files by the repo's main languages
   (most used first). Inside a language, larger files first.
2. **Drop deletion-only hunks** from a file's patch (hunks with `-` lines
   and no `+`). List fully deleted files by path instead of pasting their
   patches.
3. **Asymmetric context.** Keep more unchanged lines *before* a change
   than after. When you can read the file at the PR head, extend the
   hunk backward to the enclosing function or class (stop after a modest
   search, on the order of ten extra lines). Skip this extension for
   `.md` / `.txt`.
4. **Hunk layout.** For each kept hunk, present `__new hunk__` (new file,
   with line numbers before the change marker) then `__old hunk__` (old
   file, no line numbers, omitted when nothing was removed):

```text
## File: 'src/example.py'
@@ def save():
__new hunk__
10  unchanged
11 +added line
12  unchanged
__old hunk__
 unchanged
-removed line
 unchanged
```

   `+` appears only in `__new hunk__`; `-` only in `__old hunk__`; a
   leading space is unchanged context. Line numbers are for reference,
   not part of the source.
5. **Fill a budget, then list the rest.** Add files in the order above
   until the packed diff would leave too little room for the review
   itself. Remaining added/modified files become a name list (`other
   modified files`). Then add deleted-file names if space remains. Hard
   stop when the budget is gone; skip the rest and name them.

## Optional chunk review (up to 3)

If step 5 still leaves important files out, split the *kept* patches into
at most **three** chunks, review each with the same two passes and schema,
then merge:

- Union findings; cap shown findings at six; keep the more serious ones
- `merge_recommendation` and `risk_level`: the most severe chunk
- `estimated_effort_to_review`: the hardest chunk (do not sum)
- Union `security_concerns` (any non-`No` wins), failure modes (max 3),
  priority files, TODOs, and `can_be_split` slices
- `relevant_tests`: `Yes` if any chunk says `Yes`

Say what each chunk covered and what remains unreviewed.

## Say what you omitted

End the summary with what was dropped: deletion-only hunks, deleted files
listed by name only, leftover file names, and files never packed. If you
cannot extend a hunk to its enclosing function, say so rather than
guessing names from outside the hunk.
