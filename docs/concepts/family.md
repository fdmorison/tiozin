# Tiozin Family: Understanding Tios and Tiozins

<p align="center">
  <img
    src="https://raw.githubusercontent.com/fdmorison/tiozin/main/docs/img/tiozin_family.jpeg"
    alt="Tiozin Family"
  />
</p>

When we say **Tiozin Family**, it's not just a cute name. It's the architectural
model behind the entire framework, and the banner above captures it perfectly.

- The larger characters are the **Tios and Tias**,
- the smaller ones are the **Tiozins**.

This metaphor defines how the system is structured, how it grows, and how you extend it.

## 🧔 What is a Tio or Tia?

A **Tio** or **Tia** is a provider family. Think of it as a technological
domain with its own runtime, conventions, and set of plugins.

- Tio Spark brings distributed programatic or SQL processing,
- Tio DuckDB brings fast single-node SQL processing,
- Tia Google could bring cloud-native integrations.

Each Tio decides how it connects to data systems, what execution rules apply,
and which plugins it offers. It doesn't execute work directly; it creates and
maintains its members, the Tiozins.

Many families together form the ecosystem, and it grows naturally as new ones
appear. You're free to create your own, public or private, with whatever name
you like. Tio Dilbert, Tia Maria, whatever feels right. Nothing stops you :)

## 👶 What is a Tiozin?

A **Tiozin** is a plugin offered by a Tio or Tia, and the smallest unit of
work in the ecosystem. If it's in the execution model, it's a Tiozin. If it's
pluggable, it's a Tiozin. Jobs, Runners, Inputs, Outputs, Transforms,
metadata registries... all Tiozins.

Each one should do one thing well: small, specialized, composable, and testable.
The real power comes from composing many focused plugins together.

Like in any family, Tiozins inherit traits from their Tio. A Spark Tiozin
depends on the Spark runtime, a DuckDB Tiozin depends on DuckDB, and so on.
You can even see it in the banner: Spark Tiozins hold a spark in their hands,
SQL Tiozins carry a SQL sign, DuckDB Tiozins carry a little duck, and Bean
Tiozins carry coffee beans. They belong to their family, and they look the part.

## 🌱 The Big Will

Tiozin doesn't want to do everything. It exists to connect things.

It's the glue between
independent provider families, allowing the ecosystem to scale through
open-source collaboration:
- provider families should evolve independently,
- plugins should multiply and specialize,
- and everything stays modular, replaceable, and testable.

No monolith. Just explicit families and pluggable members.

You're welcome to contribute to the core and to build your own providers. And if Tiozin makes a difference in your work, you're welcome to reference it ❤️

## ✨ In One Line

A **Tio** provides. A **Tiozin** executes. And everything belongs to a family.
