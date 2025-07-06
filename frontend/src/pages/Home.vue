<template>
  <div class="min-h-screen bg-gray-900">
    <!-- Navigation -->
    <nav class="bg-gray-900/80 backdrop-blur-sm fixed w-full z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <img class="h-8 w-8" src="/logo.png" alt="Koura DZ" />
            </div>
            <div class="hidden md:block">
              <div class="ml-10 flex items-baseline space-x-4">
                <a href="#" class="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Le jeu</a>
                <a href="#" class="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Communauté</a>
                <a href="#" class="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Actualités</a>
              </div>
            </div>
          </div>
          <div class="flex items-center">
            <button class="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-md text-sm font-medium">
              Nous rejoindre
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- Hero Section -->
    <div class="relative overflow-hidden">
      <!-- Background Image -->
      <div class="absolute inset-0">
        <img src="/stadium.jpg" alt="Stadium" class="w-full h-full object-cover" />
        <div class="absolute inset-0 bg-gray-900/70"></div>
      </div>

      <!-- Content -->
      <div class="relative max-w-7xl mx-auto px-4 py-32 sm:px-6 lg:px-8 min-h-screen flex flex-col justify-center">
        <div class="text-center">
          <div class="flex items-center justify-center space-x-2 mb-8">
            <img src="/player-avatar.jpg" alt="Player" class="w-8 h-8 rounded-full" />
            <span class="text-gray-400">+2500 joueurs déjà prêts à entrer sur le terrain</span>
          </div>
          
          <h1 class="text-6xl font-bold tracking-tight text-white sm:text-5xl md:text-6xl lg:text-7xl">
            Une nouvelle manière de<br />vivre le football
          </h1>
          
          <p class="mt-6 max-w-2xl mx-auto text-xl text-gray-300">
            Le premier site d'organisation de matchs de football en Algérie.
            Trouve des matchs, rejoins des équipes, et vis ta passion.
          </p>
          
          <div class="mt-10 flex justify-center gap-4">
            <button class="bg-orange-500 hover:bg-orange-600 text-white px-8 py-3 rounded-full text-lg font-semibold transition-all">
              Se pré-inscrire
            </button>
            <button class="bg-white/10 hover:bg-white/20 text-white px-8 py-3 rounded-full text-lg font-semibold transition-all flex items-center">
              <span>Rejoindre</span>
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 ml-2" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Home'
}
</script>

<style>
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css');
</style>
