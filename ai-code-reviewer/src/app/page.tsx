import Image from "next/image";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <p className="fixed left-0 top-0 flex w-full justify-center border-b border-gray-300 bg-linear-to-b from-zinc-200 pb-6 pt-8 backdrop-blur-sm dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit lg:static lg:w-auto lg:rounded-xl lg:border lg:bg-gray-200 lg:p-4 lg:dark:bg-zinc-800/30">
          Get started by editing&nbsp;
          <code className="font-mono font-bold">src/app/page.tsx</code>
        </p>
      </div>

      <div className="relative flex place-items-center before:absolute before:h-75 before:w-120 before:-translate-x-1/2 before:rounded-full before:bg-gradient-radial before:from-white before:to-transparent before:blur-2xl before:content-[''] after:absolute after:-z-20 after:h-45 after:w-60 after:translate-x-1/3 after:bg-gradient-conic after:from-sky-200 after:via-blue-200 after:to-transparent after:blur-2xl after:content-[''] before:dark:bg-linear-to-br before:dark:from-transparent before:dark.to-black/40 after:dark:bg-linear-to-br after:dark:from-blue-900 after:dark:via-purple-900 after:dark:to-black/40">
        <Image
          className="relative dark:invert"
          src="/next.svg"
          alt="Next.js logo"
          width={180}
          height={37}
          priority
        />
      </div>

      <div className="mb-32 grid text-center lg:max-w-lg lg:w-full lg:text-left">
        <h1 className="text-2xl font-bold">Welcome to Next.js!</h1>
        <p className="text-lg leading-relaxed text-gray-600 dark:text-gray-400">
          This is a simple example of a Next.js app.
        </p>
      </div>
    </main>
  );
}
