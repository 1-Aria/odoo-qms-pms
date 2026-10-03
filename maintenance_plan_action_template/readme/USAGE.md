1. Define the templates under *Management System → Configuration → Action Templates*. Give each a
   **response type**: a template without one is skipped.
2. Add them on the maintenance plan's **Action Templates** page.

Every request the plan generates from then on carries one action per template, visible from the
request's *Actions* button and due on the request's scheduled date. A request raised by hand with a
plan set gets them too.

- Changing a plan's templates does not reach requests it has already generated.
- A plan generates its requests up to its horizon ahead, so their actions appear at once, each due
  on its own request's date.
- The actions are created whoever runs the generation, including a maintenance user outside the
  management system.
